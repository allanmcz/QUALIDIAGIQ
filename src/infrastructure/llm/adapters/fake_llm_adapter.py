"""
Adapter LLM fake — sem rede, respostas determinísticas para testes.

Camada: Infrastructure
"""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.llm_task_type import LlmTaskType


class FakeLlmAdapter:
    """Simula conclusão de modelo sem chamadas HTTP/SDK."""

    async def complete(self, request: LlmGatewayRequest) -> str:
        """Gera texto sintético que satisfaz guardrails mínimos de citação."""
        if request.task_type == LlmTaskType.EXPLICACAO_SCORE:
            score = request.input_data.get("score_geral", request.input_data.get("score"))
            dim = request.input_data.get("dimensao_mais_critica", "fiscal")
            return (
                f"Parecer (fake): com score {score}/100, a prontidão à Reforma do Consumo é moderada. "
                f"A dimensão {dim} concentra o maior risco imediato — recomendo plano de adequação "
                "fiscal-operacional antes de 2026. "
                "Base normativa: EC 132/2023; LC 214/2025; ABNT NBR 17301:2026."
            )
        if request.task_type == LlmTaskType.ANALISE_NORMATIVA_RAG:
            partes = [f"Conforme {e.dispositivo} ({e.fonte})." for e in request.evidencias]
            return " ".join(partes) + " Resumo adicional sintético (fake)."
        return f"[fake-llm] task={request.task_type} prompt_key={request.prompt_key}"
