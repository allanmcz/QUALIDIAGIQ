"""Testes do prompt dedicado explicacao_score."""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.adapters.llm_explicacao_score_prompt import montar_prompt_explicacao_score


class TestMontarPromptExplicacaoScore:
    """Prompt não deve pedir recomendação genérica de finalização."""

    def test_inclui_score_e_dimensoes(self) -> None:
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="explicacao_score",
            input_data={
                "score_geral": 52.0,
                "score_por_dimensao": {"fiscal": 42.0},
                "empresa_porte": "micro",
            },
        )
        prompt = montar_prompt_explicacao_score(req)
        assert "52.0" in prompt
        assert "fiscal" in prompt
        assert "NÃO recalcule o score" in prompt
        assert "LC 214/2025" in prompt

    def test_inclui_pesos_e_base_normativa(self) -> None:
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="explicacao_score",
            input_data={
                "score_geral": 60.0,
                "score_por_dimensao": {},
                "pesos_por_dimensao": {"fiscal": 1.5},
                "base_normativa": "LC 214/2025 art. 9º",
            },
        )
        prompt = montar_prompt_explicacao_score(req)
        assert "Pesos macro aplicados por dimensão" in prompt
        assert "peso 1.5" in prompt
        assert "parecer" in prompt.lower()
        assert "EC 132/2023" in prompt
