"""
Agregador de rotas HTTP públicas e de painel sob ``/diagnosticos``.

Camada: Presentation
Responsabilidade: apenas composição via ``include_router`` — helpers ficam em ``diagnostico_helpers``;
self-service e core são routers separados registados em ``main.py``.
"""

from __future__ import annotations

from fastapi import APIRouter

from src.presentation.api.routers.diagnostico_painel_router import (
    router as diagnostico_painel_router,
)
from src.presentation.api.routers.diagnostico_public_router import (
    router as diagnostico_public_router,
)

router = APIRouter(prefix="/diagnosticos")
router.include_router(diagnostico_public_router, tags=["Diagnósticos"])
router.include_router(diagnostico_painel_router, tags=["Diagnósticos"])
