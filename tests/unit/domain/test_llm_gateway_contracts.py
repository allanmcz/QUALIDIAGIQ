"""Contratos mínimos do port ``LlmGateway`` e value objects (domain)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from src.domain.ports.llm_gateway import LlmGatewayRequest, LlmGatewayResponse
from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType


class TestEvidenceRef:
    """Invariantes do value object ``EvidenceRef``."""

    def test_imutavel(self) -> None:
        ev = EvidenceRef(fonte="Lexiq", titulo="LC 214", dispositivo="art. 5º")
        with pytest.raises(FrozenInstanceError):
            ev.fonte = "x"  # type: ignore[misc]


class TestLlmGatewayRequest:
    """Montagem mínima de pedido canónico."""

    def test_request_com_evidencias(self) -> None:
        ev = EvidenceRef(fonte="Lexiq", titulo="Teste", dispositivo="LC 214/2025 art. 1º")
        req = LlmGatewayRequest(
            tenant_id="33333333-3333-4333-8333-333333333333",
            trace_id="trace-1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag.v1",
            input_data={"pergunta": "x"},
            evidencias=(ev,),
        )
        assert len(req.evidencias) == 1


class TestLlmGatewayResponse:
    """Campos de auditoria por omissão."""

    def test_guardrail_status_default(self) -> None:
        r = LlmGatewayResponse(
            text="ok",
            provider="fake",
            model="m",
            policy_version="2026-05-15-v1",
        )
        assert r.guardrail_status == "ok"
        assert r.blocked_by_guardrail is False
