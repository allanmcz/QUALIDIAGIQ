"""
Ponto de entrada do FastAPI (QualiDiagIQ API).

Camada: Presentation
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.presentation.api.routers import diagnostico_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ciclo de vida da aplicação (startup e shutdown)."""
    # TODO: Inicializar pool de conexões e clients aqui
    yield
    # TODO: Fechar conexões aqui


def create_app() -> FastAPI:
    """Factory de criação da API com injeção de rotas."""
    app = FastAPI(
        title="QualiDiagIQ API",
        description="Motor de Diagnóstico Tributário para a Reforma do Consumo.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Segurança CORS (MVP)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção: restringir para o domínio do tributiq
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Healthcheck simples
    @app.get("/health", tags=["Infra"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "qualidiagiq"}

    # Registrar os Routers do Domínio
    app.include_router(diagnostico_router.router)

    return app


app = create_app()
