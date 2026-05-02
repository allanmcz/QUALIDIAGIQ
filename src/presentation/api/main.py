"""
Ponto de entrada do FastAPI (QualiDiagIQ API).

Camada: Presentation
"""

from __future__ import annotations

from collections.abc import AsyncIterator  # noqa: TC003
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from cachetools import TTLCache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine

from src.infrastructure.config.logging import configurar_logging
from src.infrastructure.config.settings import Settings, get_settings
from src.presentation.api.middleware.idempotency import IdempotencyMiddleware
from src.presentation.api.middleware.public_rate_limit import PublicRateLimitMiddleware
from src.presentation.api.middleware.trace_context import TraceContextMiddleware
from src.presentation.api.routers import diagnostico_router

if TYPE_CHECKING:
    from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia


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
        )
    engine = None
    sync_url = settings.sync_database_url
    if sync_url:
        engine = create_engine(sync_url, pool_pre_ping=True)
    app.state.idempotency_engine = engine
    app.state.idempotency_ttl_seconds = settings.idempotency_ttl_seconds

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
        ],
        expose_headers=["X-Idempotent-Replay", "X-Trace-Id"],
    )
    app.add_middleware(IdempotencyMiddleware, cache=idempotency_cache)
    app.add_middleware(TraceContextMiddleware)
    app.add_middleware(PublicRateLimitMiddleware)

    # Healthcheck simples
    @app.get("/health", tags=["Infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "qualidiagiq"}

    # Registrar os Routers do Domínio
    from src.presentation.api.routers import auth_router, cnae_router, normativa_router

    app.include_router(diagnostico_router.router)
    app.include_router(auth_router.router)
    app.include_router(normativa_router.router)
    app.include_router(cnae_router.router)

    if settings.otel_tracing_enabled:
        _instrumentar_otel(app, settings)

    return app


app = create_app()
