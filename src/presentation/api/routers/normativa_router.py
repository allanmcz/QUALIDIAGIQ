"""
Rotas auxiliares de normativo / guardrail Lexiq (protótipo).

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
    Verifica se o texto contém âncora normativa reconhecível (heurística MVP).

    Base: princípio Tributiq — sem citação válida da Lexiq em fluxos futuros, resposta é rejeitada.
    """
    ok = texto_tem_ancora_normativa(payload.texto)
    return ValidarAncoraNormativaResponse(
        valido=ok,
        motivo_rejeicao=None if ok else mensagem_rejeicao_guardrail(),
    )
