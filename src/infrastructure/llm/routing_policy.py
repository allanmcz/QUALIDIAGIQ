"""
Política determinística de roteamento LLM (MVP técnico).

Camada: Infrastructure
Versão fixa inicial — evolução YAML em Beta (ADR-022).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.llm_task_type import LlmTaskType


@dataclass(frozen=True, slots=True)
class LlmRouteDecision:
    """Resultado da política antes de invocar adapter."""

    blocked: bool
    block_reason: str | None
    profile: str


class RoutingPolicy:
    """Regras determinísticas por ``LlmTaskType``."""

    policy_version = "2026-05-15-v1"

    def select_route(self, request: LlmGatewayRequest) -> LlmRouteDecision:
        """Escolhe perfil ou bloqueia antes de qualquer chamada externa."""
        if request.task_type == LlmTaskType.ANALISE_NORMATIVA_RAG:
            if not request.evidencias:
                return LlmRouteDecision(
                    blocked=True,
                    block_reason="missing_evidence",
                    profile="blocked",
                )
            return LlmRouteDecision(blocked=False, block_reason=None, profile="premium")

        if request.task_type == LlmTaskType.EXPLICACAO_SCORE:
            dados = request.input_data
            if "score_geral" not in dados and "score" not in dados:
                return LlmRouteDecision(
                    blocked=True,
                    block_reason="missing_score",
                    profile="blocked",
                )
            return LlmRouteDecision(blocked=False, block_reason=None, profile="balanced")

        if request.task_type == LlmTaskType.CLASSIFICACAO_RESPOSTA:
            return LlmRouteDecision(blocked=False, block_reason=None, profile="fast")

        return LlmRouteDecision(blocked=False, block_reason=None, profile="balanced")
