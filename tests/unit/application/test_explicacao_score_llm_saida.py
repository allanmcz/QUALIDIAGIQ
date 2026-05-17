"""Validação de parecer substantivo — explicação do score."""

from __future__ import annotations

import pytest

from src.application.services.explicacao_score_llm_saida import parecer_explicacao_score_substantivo
from src.application.services.lexiq_guardrail import filtrar_resposta_explicacao_score_llm


def test_rejeita_fallback_adapter_indisponibilidade() -> None:
    texto = (
        "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
        "personalizada não pôde ser gerada no momento."
    )
    assert not parecer_explicacao_score_substantivo(texto)


@pytest.mark.asyncio
async def test_guardrail_rejeita_fallback_adapter() -> None:
    texto = (
        "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
        "personalizada não pôde ser gerada no momento."
    )
    out = await filtrar_resposta_explicacao_score_llm(texto)
    assert out.startswith("Recomendação não exibida:")
