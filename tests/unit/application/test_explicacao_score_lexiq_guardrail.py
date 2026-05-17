"""Guardrail Lexiq específico para explicação do score (parecer, não rejeição total)."""

from __future__ import annotations

import pytest

from src.application.services.lexiq_guardrail import (
    _RODAPE_ANCORAS_EXPLICACAO_SCORE,
    filtrar_resposta_explicacao_score_llm,
    mensagem_rejeicao_guardrail,
)
from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.adapters.llm_explicacao_score_prompt import montar_prompt_explicacao_score


@pytest.mark.asyncio
async def test_explicacao_score_preserva_parecer_sem_ancora_e_apendice() -> None:
    parecer = (
        "Na minha leitura, o score indica maturidade intermediária na transição. "
        "A empresa deve priorizar adequação de cadastros e alinhamento do ERP aos novos "
        "fluxos de documentos fiscais antes do cronograma de 2026."
    )
    out = await filtrar_resposta_explicacao_score_llm(parecer)
    assert parecer in out
    assert "EC 132/2023" in out
    assert _RODAPE_ANCORAS_EXPLICACAO_SCORE in out
    assert not out.startswith("Recomendação não exibida:")


@pytest.mark.asyncio
async def test_explicacao_score_texto_curto_rejeita() -> None:
    out = await filtrar_resposta_explicacao_score_llm("Muito baixo.")
    assert out == mensagem_rejeicao_guardrail()


def test_prompt_explicacao_score_pedir_parecer_e_dados() -> None:
    req = LlmGatewayRequest(
        tenant_id="t",
        trace_id="tr",
        task_type=LlmTaskType.EXPLICACAO_SCORE,
        prompt_key="explicacao_score",
        input_data={
            "score_geral": 54.9,
            "empresa_razao_social": "OLIVEIRA LTDA",
            "nivel_maturidade": "intermediario",
            "dimensao_mais_critica": "Contábil",
            "score_por_dimensao": {"fiscal": 40.0, "contabil": 17.9},
        },
    )
    prompt = montar_prompt_explicacao_score(req)
    assert "parecer" in prompt.lower() or "opinião" in prompt.lower()
    assert "OLIVEIRA LTDA" in prompt
    assert "54.9" in prompt
    assert "LC 214/2025" in prompt
    assert "NÃO recalcule" in prompt
