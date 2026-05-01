"""
Rotas auxiliares de normativo — protótipo de âncoras (análise ANALISE §E1/E2).

Não equivale ao motor Lexiq com RAG e citação a fontes versionadas (princípio tributiq roadmap).
Para disclosure ao usuario final usar os mesmos avisos do OpenAPI schemas + front wizard.

Camada: Presentation
"""

from typing import Annotated

from fastapi import APIRouter, Body

from src.application.services.lexiq_guardrail import (
    mensagem_rejeicao_guardrail,
    texto_tem_ancora_normativa,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_NORMATIVA
from src.presentation.api.schemas import (
    ValidarAncoraNormativaRequest,
    ValidarAncoraNormativaResponse,
)

router = APIRouter(prefix="/normativa", tags=["Lexiq / guardrails"])


@router.post("/validar-ancora", response_model=ValidarAncoraNormativaResponse)
async def validar_ancora_normativa(
    payload: Annotated[
        ValidarAncoraNormativaRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_NORMATIVA)),
    ],
) -> ValidarAncoraNormativaResponse:
    """
    Checagem heurística apenas (padrões tipo LC / EC / ABNT em texto corrido).

    Disclaimer: não avalia suficiência legal nem substitui análise profissional; fluxos Lexiq formais futuros
    rejeitarão lacunas segundo política tributiq configurada (LC 214/2025 — transparência contribuinte).
    """
    ok = texto_tem_ancora_normativa(payload.texto)
    return ValidarAncoraNormativaResponse(
        valido=ok,
        motivo_rejeicao=None if ok else mensagem_rejeicao_guardrail(),
    )
