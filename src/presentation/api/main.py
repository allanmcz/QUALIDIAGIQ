"""
Ponto de entrada do FastAPI (QualiDiagIQ API).

Camada: Presentation
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator  # noqa: TC003
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

import structlog
from cachetools import TTLCache
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from starlette.requests import Request  # noqa: TC002 — runtime para FastAPI Depends/injeção

from src.domain.entities.diagnostico import DiagnosticoNaoFinalizavelError
from src.infrastructure.config.logging import configurar_logging
from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.api.middleware.idempotency import IdempotencyMiddleware
from src.presentation.api.middleware.public_rate_limit import PublicRateLimitMiddleware
from src.presentation.api.middleware.sensitive_route_rate_limit import (
    SensitiveRouteRateLimitMiddleware,
)
from src.presentation.api.middleware.trace_context import TraceContextMiddleware
from src.presentation.api.routers import diagnostico_router

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia


def _sentry_scrub_pii(event: Any, hint: dict[str, Any]) -> Any:
    """QDI-H-016 — reduz vazamento de PII em extras/request/user (melhor esforço, não substitui DLP)."""
    _ = hint
    chaves_sensiveis = (
        "password",
        "senha",
        "codigo",
        "token",
        "authorization",
        "email",
        "e-mail",
        "telefone",
        "celular",
        "otp",
        "cpf",
    )
    try:
        if not isinstance(event, dict):
            return event
        req = event.get("request")
        if isinstance(req, dict):
            data = req.get("data")
            if isinstance(data, dict):
                for k in list(data.keys()):
                    if any(s in str(k).lower() for s in chaves_sensiveis):
                        data[k] = "[REDACTED]"
        user = event.get("user")
        if isinstance(user, dict):
            for k in ("email", "username", "ip_address", "telefone", "celular", "phone"):
                if k in user:
                    user[k] = "[REDACTED]"
        extra = event.get("extra")
        if isinstance(extra, dict):
            for k in list(extra.keys()):
                if any(s in str(k).lower() for s in chaves_sensiveis):
                    extra[k] = "[REDACTED]"
    except Exception:
        pass
    return event


def _ping_db_sync(eng: Engine) -> None:
    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))


def _parse_otlp_headers(raw: str | None) -> dict[str, str] | None:
    """Parse `OTEL_EXPORTER_OTLP_HEADERS` no formato `k=v,k2=v2`."""
    if not raw or not str(raw).strip():
        return None
    out: dict[str, str] = {}
    for part in str(raw).split(","):
        p = part.strip()
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip()] = v.strip().strip('"')
    return out or None


def _derive_otlp_metrics_endpoint(trace_endpoint: str) -> str | None:
    """Deriva URL OTLP/HTTP de métricas a partir do endpoint de traces (mesmo host/collector)."""
    raw = trace_endpoint.strip()
    if not raw:
        return None
    if "/v1/traces" in raw:
        return raw.replace("/v1/traces", "/v1/metrics")
    base = raw.rstrip("/")
    return f"{base}/v1/metrics"


def _instrumentar_otel(app: FastAPI, settings: Settings) -> None:
    """
    OpenTelemetry — console em dev ou OTLP/HTTP quando `OTEL_EXPORTER_OTLP_ENDPOINT` está definido.

    Smoke staging: enviar uma requisição GET /health com trace habilitado e verificar span no collector.
    """
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    endpoint = (settings.otel_exporter_otlp_endpoint or "").strip()
    if endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(
            endpoint=endpoint,
            headers=_parse_otlp_headers(settings.otel_exporter_otlp_headers),
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    metrics_url = _derive_otlp_metrics_endpoint(endpoint)
    if metrics_url:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

        from src.presentation.api.middleware.otel_http_metrics import OtelHttpMetricsMiddleware

        metric_exporter = OTLPMetricExporter(
            endpoint=metrics_url,
            headers=_parse_otlp_headers(settings.otel_exporter_otlp_headers),
        )
        reader = PeriodicExportingMetricReader(metric_exporter)
        meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
        otel_metrics.set_meter_provider(meter_provider)
        meter = otel_metrics.get_meter(settings.otel_service_name)
        app.add_middleware(OtelHttpMetricsMiddleware, meter=meter)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida da aplicação (startup e shutdown)."""
    settings = get_settings()
    configurar_logging(settings.app_env)
    dsn_sentry = (settings.sentry_dsn or "").strip()
    if dsn_sentry:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn_sentry,
            traces_sample_rate=0.1,
            environment=(settings.app_env or "development").strip(),
            before_send=_sentry_scrub_pii,
        )
    engine = None
    sync_url = settings.sync_database_url
    if sync_url:
        engine = create_engine(sync_url, pool_pre_ping=True)
    app.state.idempotency_engine = engine
    app.state.idempotency_ttl_seconds = settings.idempotency_ttl_seconds
    app.state.idempotency_backend_active = engine is not None
    logger.info(
        "idempotency_backend_startup",
        idempotency_backend_active=bool(engine),
        app_env=(settings.app_env or "").strip(),
    )

    env_norm = (settings.app_env or "").strip().lower()
    if env_norm != "development" and engine is None:
        raise RuntimeError(
            "QDI-H-037: `DATABASE_URL` obrigatório para backend de idempotência em Postgres "
            f"quando APP_ENV={settings.app_env!r} (memória apenas permitida em development)."
        )

    yield

    if engine is not None:
        engine.dispose()


def create_app() -> FastAPI:
    """Factory de criação da API com injeção de rotas."""
    tags_metadata = [
        {
            "name": "Diagnósticos",
            "description": "Criação, consulta e geração de relatórios de diagnósticos tributários (ABNT NBR 17301).",
        },
        {
            "name": "Infra",
            "description": "Endpoints de infraestrutura e healthchecks.",
        },
        {
            "name": "Lexiq / guardrails",
            "description": (
                "Protótipo (heurístico) de checagem de âncoras normativas na redação — não é RAG Lexiq "
                "completo nem parecer jurídico consultivo (LC 214/2025 — boa fé informacional). "
                "Ver ADR UX no repositório .github quando integrar baseline Lexiq oficial."
            ),
        },
        {
            "name": "Referência CNAE",
            "description": (
                "Consulta somente leitura CNAE 2.3 (schema qdi, CONCLA/IBGE). "
                "Público; exige DATABASE_URL no backend. Rate limit por IP (middleware público)."
            ),
        },
        {
            "name": "Referência CNPJ",
            "description": (
                "Consulta cadastral CNPJ com cache TTL triplo (env), BrasilAPI e fallback Minha Receita. "
                "Autenticado (JWT); Idempotency-Key obrigatória."
            ),
        },
        {
            "name": "Privacidade LGPD",
            "description": (
                "Solicitações operacionais de direitos do titular (Lei 13.709/2018 art. 18) "
                "no tenant autenticado."
            ),
        },
    ]

    app = FastAPI(
        title="QualiDiagIQ API",
        description="""
        Motor de Diagnóstico Tributário Automatizado para a Reforma do Consumo.
        
        Parte do ecossistema Tributiq. Fornece análise de maturidade e conformidade
        com base na EC 132/2023, LC 214/2025 e ABNT NBR 17301:2026.
        """,
        version="0.1.0",
        contact={
            "name": "Equipe Tributiq",
            "email": "contato@tributiq.com.br",
        },
        openapi_tags=tags_metadata,
        lifespan=lifespan,
    )

    settings = get_settings()
    idempotency_cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(
        maxsize=settings.idempotency_max_entries,
        ttl=settings.idempotency_ttl_seconds,
    )
    app.state.idempotency_cache = idempotency_cache

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Idempotency-Key",
            "If-Match",
            "X-Trace-Id",
            "X-Rascunho-Token",
            "traceparent",
            "tracestate",
        ],
        expose_headers=["X-Idempotent-Replay", "X-Trace-Id"],
    )
    app.add_middleware(IdempotencyMiddleware, cache=idempotency_cache)
    app.add_middleware(TraceContextMiddleware)
    app.add_middleware(PublicRateLimitMiddleware)
    app.add_middleware(SensitiveRouteRateLimitMiddleware)

    @app.exception_handler(DiagnosticoNaoFinalizavelError)
    async def diagnostico_nao_finalizavel_handler(
        _request: Request, exc: DiagnosticoNaoFinalizavelError
    ) -> JSONResponse:
        """
        Conflito de estado do agregado (ex.: PATCH em diagnóstico não finalizado).

        HTTP 409 — semântica adequada a «recurso existe mas transição ilegal» (vs 400 genérico).
        """
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    # Healthcheck simples (legado — preferir /health/live e /health/ready).
    @app.get("/health", tags=["Infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "qualidiagiq"}

    @app.get("/health/live", tags=["Infra"])
    async def health_live() -> dict[str, str]:
        """Liveness — processo UP (Kubernetes)."""
        return {"status": "ok", "check": "live", "service": "qualidiagiq"}

    @app.get("/health/ready", tags=["Infra"], response_model=None)
    async def health_ready(request: Request) -> dict[str, str] | JSONResponse:
        """Readiness — Postgres acessível via engine síncrono (idempotência)."""
        eng = getattr(request.app.state, "idempotency_engine", None)
        if eng is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "reason": "database_unconfigured"},
            )
        try:
            await asyncio.to_thread(_ping_db_sync, eng)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "reason": "database_unreachable"},
            )
        return {
            "status": "ok",
            "check": "ready",
            "service": "qualidiagiq",
            "idempotency_backend": "postgres",
        }

    @app.get("/health/llm", tags=["Infra"])
    async def health_llm() -> dict[str, str]:
        """Saúde do backend LLM (Ollama / router / Bedrock flag) — ADR-022 Fase 4."""
        from src.infrastructure.config.settings import get_settings
        from src.infrastructure.llm.llm_health_probe import probe_llm_health

        return probe_llm_health(get_settings())

    # Registrar os Routers do Domínio
    from src.presentation.api.routers import (
        admin_maintenance_router,
        auth_router,
        cnae_router,
        cnpj_router,
        diagnostico_core_router,
        diagnostico_self_service_router,
        mock_storage_router,
        normativa_router,
        privacidade_router,
        public_institucional_router,
    )

    app.include_router(public_institucional_router.router)
    app.include_router(diagnostico_router.router)
    app.include_router(diagnostico_self_service_router.router)
    app.include_router(diagnostico_core_router.router)
    app.include_router(auth_router.router)
    app.include_router(admin_maintenance_router.router)
    app.include_router(normativa_router.router)
    app.include_router(cnae_router.router)
    app.include_router(cnpj_router.router)
    app.include_router(privacidade_router.router)
    app.include_router(mock_storage_router.router)

    if settings.otel_tracing_enabled:
        _instrumentar_otel(app, settings)

    return app


app = create_app()
