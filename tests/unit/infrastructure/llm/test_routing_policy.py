"""Testes da ``RoutingPolicy`` (ADR-022)."""

from __future__ import annotations

import pytest

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.llm.routing_policy import RoutingPolicy


def _req(
    task: LlmTaskType,
    *,
    evidencias: tuple[EvidenceRef, ...] = (),
    input_data: dict | None = None,
) -> LlmGatewayRequest:
    return LlmGatewayRequest(
        tenant_id="t1",
        trace_id="tr",
        task_type=task,
        prompt_key="p",
        input_data=input_data or {},
        evidencias=evidencias,
    )


class TestRoutingPolicy:
    """Política determinística por tipo de tarefa."""

    def test_rag_sem_evidencia_bloqueia(self) -> None:
        pol = RoutingPolicy()
        d = pol.select_route(_req(LlmTaskType.ANALISE_NORMATIVA_RAG))
        assert d.blocked is True
        assert d.block_reason == "missing_evidence"

    def test_rag_com_evidencia_permite(self) -> None:
        pol = RoutingPolicy()
        ev = EvidenceRef(fonte="f", titulo="t", dispositivo="art. 1º")
        d = pol.select_route(_req(LlmTaskType.ANALISE_NORMATIVA_RAG, evidencias=(ev,)))
        assert d.blocked is False
        assert d.profile == "premium"

    def test_explicacao_score_sem_score_bloqueia(self) -> None:
        pol = RoutingPolicy()
        d = pol.select_route(_req(LlmTaskType.EXPLICACAO_SCORE, input_data={}))
        assert d.blocked is True
        assert d.block_reason == "missing_score"

    @pytest.mark.parametrize("chave", ["score_geral", "score"])
    def test_explicacao_score_com_score_permite(self, chave: str) -> None:
        pol = RoutingPolicy()
        d = pol.select_route(_req(LlmTaskType.EXPLICACAO_SCORE, input_data={chave: 73.0}))
        assert d.blocked is False

    def test_policy_version_fixa(self) -> None:
        assert RoutingPolicy.policy_version == "2026-05-15-v1"

    def test_classificacao_resposta_perfil_rapido(self) -> None:
        pol = RoutingPolicy()
        d = pol.select_route(_req(LlmTaskType.CLASSIFICACAO_RESPOSTA))
        assert d.blocked is False
        assert d.profile == "fast"

    def test_relatorio_executivo_perfil_balanceado_padrao(self) -> None:
        pol = RoutingPolicy()
        d = pol.select_route(_req(LlmTaskType.RELATORIO_EXECUTIVO))
        assert d.blocked is False
        assert d.profile == "balanced"
