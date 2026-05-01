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

from src.infrastructure.config.settings import get_settings
from src.presentation.api.middleware.idempotency import IdempotencyMiddleware
from src.presentation.api.routers import diagnostico_router

if TYPE_CHECKING:
    from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia


def _instrumentar_otel(app: FastAPI, service_name: str) -> None:
    """OpenTelemetry mínimo — export console em desenvolvimento (ativar via OTEL_TRACING_ENABLED)."""
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida da aplicação (startup e shutdown)."""
    settings = get_settings()
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
            "description": "Validação mínima de âncoras normativas (protótipo S02).",
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
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key", "If-Match"],
        expose_headers=["X-Idempotent-Replay"],
    )
    app.add_middleware(IdempotencyMiddleware, cache=idempotency_cache)

    # Healthcheck simples
    @app.get("/health", tags=["Infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "qualidiagiq"}

    # Registrar os Routers do Domínio
    from src.presentation.api.routers import auth_router, normativa_router

    app.include_router(diagnostico_router.router)
    app.include_router(auth_router.router)
    app.include_router(normativa_router.router)

    if settings.otel_tracing_enabled:
        _instrumentar_otel(app, settings.otel_service_name)

    return app


app = create_app()
