"""
Ponto de entrada do FastAPI (QualiDiagIQ API).

Camada: Presentation
"""

from __future__ import annotations

from collections.abc import AsyncIterator  # noqa: TC003
from contextlib import asynccontextmanager

from cachetools import TTLCache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.config.settings import get_settings
from src.presentation.api.middleware.idempotency import (
    CorpoCacheadoIdempotencia,
    IdempotencyMiddleware,
)
from src.presentation.api.routers import diagnostico_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida da aplicação (startup e shutdown)."""
    # TODO: Inicializar pool de conexões e clients aqui
    yield
    # TODO: Fechar conexões aqui


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
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
        expose_headers=["X-Idempotent-Replay"],
    )
    app.add_middleware(IdempotencyMiddleware, cache=idempotency_cache)

    # Healthcheck simples
    @app.get("/health", tags=["Infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "qualidiagiq"}

    # Registrar os Routers do Domínio
    from src.presentation.api.routers import auth_router

    app.include_router(diagnostico_router.router)
    app.include_router(auth_router.router)

    return app


app = create_app()
