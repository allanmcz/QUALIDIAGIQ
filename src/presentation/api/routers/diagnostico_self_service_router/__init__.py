"""
Rotas HTTP de self-service para Diagnóstico.

Camada: Presentation
Responsabilidade: fluxo sem sessão na plataforma (rascunho + OTP + conclusão + vinculação).
"""

from __future__ import annotations

from fastapi import APIRouter

from .routes_rascunho import router as rascunho_router
from .routes_self_service_post import router as self_service_post_router
from .routes_vinculos import router as vinculos_router

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])
router.include_router(self_service_post_router)
router.include_router(rascunho_router)
router.include_router(vinculos_router)

__all__ = ["router"]
