"""
Caso de uso — explicação narrativa do score via gateway LLM (**ADR-022**).

Camada: Application
Não recalcula o score 0-100 (motor determinístico); apenas orquestra ``LlmGateway``.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID  # noqa: TC003 — dataclass de comando usa UUID em runtime

from src.domain.ports.llm_gateway import LlmGateway, LlmGatewayRequest, LlmGatewayResponse
from src.domain.value_objects.llm_task_type import LlmTaskType


@dataclass(frozen=True)
class ComandoExplicarScoreLlm:
    """Entrada mínima para narrativa sobre o score já calculado."""

    tenant_id: UUID
    trace_id: str
    score_geral: float
    campos_extras: dict[str, object] | None = None


class ExplicarScoreLlmUseCase:
    """Delega ao ``LlmGateway`` com tipo ``EXPLICACAO_SCORE`` (política + guardrails na infra)."""

    def __init__(self, gateway: LlmGateway) -> None:
        self._gateway = gateway

    async def execute(self, comando: ComandoExplicarScoreLlm) -> LlmGatewayResponse:
        """Invoca o gateway; respeita bloqueios e metadados de auditoria na resposta."""
        extras = comando.campos_extras or {}
        req = LlmGatewayRequest(
            tenant_id=str(comando.tenant_id),
            trace_id=comando.trace_id,
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="explicacao_score",
            input_data={"score_geral": comando.score_geral, **extras},
        )
        return await self._gateway.complete(req)
