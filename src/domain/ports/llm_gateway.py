"""
Port do gateway LLM governado (router convergente).

Camada: Domain
Contrato canónico de pedido/resposta — sem FastAPI, sem SDK, sem I/O.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType


@dataclass(frozen=True, slots=True)
class LlmGatewayRequest:
    """Entrada canónica de uma tarefa de IA."""

    tenant_id: str
    trace_id: str
    task_type: LlmTaskType
    prompt_key: str
    input_data: dict[str, object]
    evidencias: tuple[EvidenceRef, ...] = ()
    max_output_tokens: int | None = None
    temperatura: float = 0.2
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class LlmGatewayResponse:
    """Resposta canónica com metadados de auditoria."""

    text: str
    provider: str
    model: str
    policy_version: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    blocked_by_guardrail: bool = False
    guardrail_reason: str | None = None
    guardrail_status: str = "ok"
    #: Trechos recuperados (Lexiq/RAG) para auditoria e UI — Onda IA 1.1.
    fontes_rag: tuple[dict[str, object], ...] = ()
    #: ``com_fonte`` | ``base_insuficiente`` | ``nao_recuperado`` | ``nao_aplicavel``.
    rag_status: str = "nao_aplicavel"


class LlmGateway(ABC):
    """Porta para execução de tarefas LLM com política e guardrails na infra."""

    @abstractmethod
    async def complete(self, request: LlmGatewayRequest) -> LlmGatewayResponse:
        """Executa a tarefa (router + guardrail + adapter)."""
        raise NotImplementedError
