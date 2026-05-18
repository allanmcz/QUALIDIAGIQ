"""
Caso de uso — explicação narrativa do score via gateway LLM (**ADR-022**).

Camada: Application
Não recalcula o score 0-100 (motor determinístico); orquestra RAG + ``LlmGateway``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID  # noqa: TC003 — dataclass de comando usa UUID em runtime

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.services.explicacao_score_rag import (
    RAG_STATUS_NAO_RECUPERADO,
    chunks_para_fontes_rag,
    formatar_rag_contexto_para_prompt,
    rag_recuperacao_insuficiente,
    recuperar_contexto_explicacao_score,
    resposta_bloqueada_base_normativa_insuficiente,
)
from src.domain.ports.llm_gateway import LlmGateway, LlmGatewayRequest, LlmGatewayResponse
from src.domain.value_objects.llm_task_type import LlmTaskType


@dataclass(frozen=True)
class ComandoExplicarScoreLlm:
    """Entrada mínima para narrativa sobre o score já calculado."""

    tenant_id: UUID
    trace_id: str
    score_geral: float
    campos_extras: dict[str, object] | None = None
    #: Eco do header HTTP (correlação com fornecedor / auditoria ADR-022).
    idempotency_key: str | None = None


class ExplicarScoreLlmUseCase:
    """Delega ao ``LlmGateway`` com RAG opcional e tipo ``EXPLICACAO_SCORE``."""

    def __init__(
        self,
        gateway: LlmGateway,
        *,
        base_normativa_port: BaseNormativaPort | None = None,
        rag_similarity_threshold: float = 0.65,
        rag_top_k: int = 4,
        policy_version: str = "2026-05-15-v1",
    ) -> None:
        self._gateway = gateway
        self._base_normativa_port = base_normativa_port
        self._rag_threshold = float(rag_similarity_threshold)
        self._rag_top_k = max(1, min(int(rag_top_k), 10))
        self._policy_version = policy_version.strip() or "2026-05-15-v1"

    async def execute(self, comando: ComandoExplicarScoreLlm) -> LlmGatewayResponse:
        """Recupera contexto RAG, invoca gateway e anexa fontes na resposta."""
        extras: dict[str, object] = dict(comando.campos_extras or {})
        evidencias = ()
        rag_status = "nao_aplicavel"
        fontes: tuple[dict[str, object], ...] = ()

        if self._base_normativa_port is not None:
            chunks, rag_status, evidencias = await recuperar_contexto_explicacao_score(
                self._base_normativa_port,
                comando.score_geral,
                extras,
                top_k=self._rag_top_k,
                threshold=self._rag_threshold,
            )
            fontes = chunks_para_fontes_rag(chunks)
            if chunks:
                extras["rag_contexto"] = formatar_rag_contexto_para_prompt(chunks)
            extras["rag_status"] = rag_status

            if rag_recuperacao_insuficiente(rag_status):
                bloqueio = resposta_bloqueada_base_normativa_insuficiente(
                    policy_version=self._policy_version,
                )
                return replace(
                    bloqueio,
                    rag_status=rag_status,
                    fontes_rag=fontes if rag_status != RAG_STATUS_NAO_RECUPERADO else (),
                )

        req = LlmGatewayRequest(
            tenant_id=str(comando.tenant_id),
            trace_id=comando.trace_id,
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="explicacao_score",
            input_data={"score_geral": comando.score_geral, **extras},
            evidencias=evidencias,
            idempotency_key=comando.idempotency_key,
        )
        resp = await self._gateway.complete(req)
        return replace(resp, fontes_rag=fontes, rag_status=rag_status)
