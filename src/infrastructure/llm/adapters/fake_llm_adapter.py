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
            return (
                f"Explicação sintética (fake): o score já calculado pelo motor QDI foi {score}. "
                "Não é recálculo nem substituição do motor determinístico."
            )
        if request.task_type == LlmTaskType.ANALISE_NORMATIVA_RAG:
            partes = [f"Conforme {e.dispositivo} ({e.fonte})." for e in request.evidencias]
            return " ".join(partes) + " Resumo adicional sintético (fake)."
        return f"[fake-llm] task={request.task_type} prompt_key={request.prompt_key}"
