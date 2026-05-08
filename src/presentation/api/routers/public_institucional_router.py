"""
Rotas públicas institucionais (LGPD / transparência) sem JWT.

Camada: Presentation
"""

from __future__ import annotations

from fastapi import APIRouter

from src.infrastructure.config.settings import get_settings
from src.presentation.api.schemas import InstitucionalPublicResponse

router = APIRouter(prefix="/public", tags=["Institucional"])


@router.get(
    "/institucional",
    response_model=InstitucionalPublicResponse,
    summary="Dados institucionais públicos (DPO / referências LGPD)",
    description=(
        "Sem autenticação. Expõe `LGPD_DPO_EMAIL` e referência numérica de retenção (`LGPD_RETENTION_DAYS`) "
        "carregadas na API para paridade com o site (`NEXT_PUBLIC_LGPD_DPO_EMAIL`). O texto jurídico prevalece "
        "sobre estes valores em caso de divergência."
    ),
)
def obter_institucional_publico() -> InstitucionalPublicResponse:
    s = get_settings()
    email = s.lgpd_dpo_email.strip()
    return InstitucionalPublicResponse(
        lgpd_dpo_email=email or None,
        lgpd_retencao_referencia_dias=s.lgpd_retention_days,
        privacidade_solicitacoes_path="/privacidade/solicitacoes",
    )
