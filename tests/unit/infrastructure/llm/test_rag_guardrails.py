"""Testes do ``RagGuardrailService``."""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest, LlmGatewayResponse
from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.llm.guardrails.rag_guardrail_service import RagGuardrailService


class TestRagGuardrailService:
    """Entrada e saída para tarefas normativas."""

    def test_entrada_rag_sem_evidencia(self) -> None:
        svc = RagGuardrailService()
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="p",
            input_data={},
            evidencias=(),
        )
        assert svc.validate_input(req) == "rag_sem_evidencias"

    def test_entrada_relatorio_sem_contexto_executivo(self) -> None:
        svc = RagGuardrailService()
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.RELATORIO_EXECUTIVO,
            prompt_key="rel",
            input_data={},
        )
        assert svc.validate_input(req) == "contexto_executivo_obrigatorio"

    def test_entrada_relatorio_com_contexto_ok(self) -> None:
        svc = RagGuardrailService()
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.RELATORIO_EXECUTIVO,
            prompt_key="rel",
            input_data={"contexto_executivo": "Resumo para o board."},
        )
        assert svc.validate_input(req) is None

    def test_saida_bloqueada_curto_circuito(self) -> None:
        """Saída já marcada como bloqueada não revalida citação."""
        svc = RagGuardrailService()
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="p",
            input_data={},
            evidencias=(),
        )
        resp = LlmGatewayResponse(
            text="",
            provider="n",
            model="m",
            policy_version="v",
            blocked_by_guardrail=True,
        )
        assert svc.validate_output(req, resp) is None

    def test_saida_rag_sem_evidencias_na_requisicao(self) -> None:
        svc = RagGuardrailService()
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="p",
            input_data={},
            evidencias=(),
        )
        resp = LlmGatewayResponse(
            text="qualquer",
            provider="fake",
            model="fake",
            policy_version="v",
        )
        assert svc.validate_output(req, resp) == "rag_sem_evidencias"

    def test_saida_sem_dispositivo_bloqueia(self) -> None:
        svc = RagGuardrailService()
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 99º")
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="p",
            input_data={},
            evidencias=(ev,),
        )
        resp = LlmGatewayResponse(
            text="Texto sem citação útil.",
            provider="fake",
            model="fake",
            policy_version="2026-05-15-v1",
        )
        assert svc.validate_output(req, resp) == "rag_saida_sem_citacao_dispositivo"

    def test_saida_com_dispositivo_ok(self) -> None:
        svc = RagGuardrailService()
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 5º")
        req = LlmGatewayRequest(
            tenant_id="t",
            trace_id="x",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="p",
            input_data={},
            evidencias=(ev,),
        )
        resp = LlmGatewayResponse(
            text="Resumo conforme LC 214/2025 art. 5º aplicável.",
            provider="fake",
            model="fake",
            policy_version="2026-05-15-v1",
        )
        assert svc.validate_output(req, resp) is None
