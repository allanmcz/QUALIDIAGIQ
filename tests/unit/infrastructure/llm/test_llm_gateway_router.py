"""Testes do ``LlmGatewayRouter`` (Fase 1 — sem rede)."""

from __future__ import annotations

import pytest

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.config.settings import Settings
from src.infrastructure.llm.adapters.fake_llm_adapter import FakeLlmAdapter
from src.infrastructure.llm.gateway_router import LlmGatewayRouter


def _settings(**kwargs: object) -> Settings:
    base: dict[str, object] = {
        "llm_router_enabled": True,
        "llm_router_policy_version": "2026-05-15-v1",
    }
    base.update(kwargs)
    return Settings().model_copy(update=base)


class TestLlmGatewayRouter:
    """Fluxo completo política + guardrail + fake."""

    @pytest.mark.asyncio
    async def test_rag_sem_evidencia_bloqueia(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(),
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "missing_evidence"
        assert resp.policy_version == "2026-05-15-v1"

    @pytest.mark.asyncio
    async def test_rag_com_evidencia_ok(self) -> None:
        router = LlmGatewayRouter(_settings())
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 5º")
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(ev,),
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is False
        assert "LC 214/2025 art. 5º" in resp.text
        assert resp.provider == "fake"
        assert resp.model == "fake-llm"

    @pytest.mark.asyncio
    async def test_explicacao_score_sem_score_bloqueia(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="expl",
            input_data={},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "missing_score"

    @pytest.mark.asyncio
    async def test_explicacao_score_com_score_nao_recalcula(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="expl",
            input_data={"score_geral": 68.5},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is False
        assert "68.5" in resp.text
        assert "motor QDI" in resp.text

    @pytest.mark.asyncio
    async def test_flag_desligado_bloqueia(self) -> None:
        router = LlmGatewayRouter(_settings(llm_router_enabled=False))
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 1º")
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(ev,),
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "feature_disabled"

    @pytest.mark.asyncio
    async def test_relatorio_sem_contexto_bloqueia_guardrail_entrada(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.RELATORIO_EXECUTIVO,
            prompt_key="rel",
            input_data={},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "contexto_executivo_obrigatorio"

    @pytest.mark.asyncio
    async def test_relatorio_com_contexto_ok(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.RELATORIO_EXECUTIVO,
            prompt_key="rel",
            input_data={"contexto_executivo": "Síntese para stakeholders."},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is False
        assert "fake-llm" in resp.text

    @pytest.mark.asyncio
    async def test_policy_version_em_branco_usa_padrao_routing(self) -> None:
        router = LlmGatewayRouter(_settings(llm_router_policy_version="   "))
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="expl",
            input_data={"score": 50.0},
        )
        resp = await router.complete(req)
        assert resp.policy_version == "2026-05-15-v1"

    @pytest.mark.asyncio
    async def test_classificacao_resposta_ok(self) -> None:
        router = LlmGatewayRouter(_settings())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.CLASSIFICACAO_RESPOSTA,
            prompt_key="cls",
            input_data={"resposta": "sim"},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is False
        assert resp.guardrail_status == "ok"

    @pytest.mark.asyncio
    async def test_saida_guardrail_com_adapter_sem_citacao(self) -> None:
        class _FakeSemCitacao(FakeLlmAdapter):
            async def complete(self, _request: LlmGatewayRequest) -> str:
                return "Resposta genérica sem dispositivo legal."

        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 5º")
        router = LlmGatewayRouter(_settings(), fake_adapter=_FakeSemCitacao())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(ev,),
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "rag_saida_sem_citacao_dispositivo"

    @pytest.mark.asyncio
    async def test_rag_com_llm_service_simulado_cita_dispositivo(self) -> None:
        class _StubLlm:
            async def gerar_recomendacao(
                self, *, contexto_empresa: str, base_normativa: str
            ) -> str:
                _ = (contexto_empresa, base_normativa)
                return "Síntese conforme LC 214/2025 art. 5º."

        router = LlmGatewayRouter(
            _settings(llm_backend="http_ollama"),
            llm_service=_StubLlm(),
        )
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 5º")
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(ev,),
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is False
        assert "LC 214/2025 art. 5º" in resp.text
        assert resp.provider == "http_ollama"

    @pytest.mark.asyncio
    async def test_excecao_no_adapter_retorna_adapter_exception(self) -> None:
        class _BoomLlm:
            async def gerar_recomendacao(
                self, *, contexto_empresa: str, base_normativa: str
            ) -> str:
                _ = (contexto_empresa, base_normativa)
                msg = "falha simulada"
                raise RuntimeError(msg)

        router = LlmGatewayRouter(_settings(), llm_service=_BoomLlm())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.CLASSIFICACAO_RESPOSTA,
            prompt_key="cls",
            input_data={"x": 1},
        )
        resp = await router.complete(req)
        assert resp.blocked_by_guardrail is True
        assert resp.guardrail_reason == "adapter_exception"

    @pytest.mark.asyncio
    async def test_backend_openai_reflecte_modelo_nas_metas(self) -> None:
        class _StubLlm:
            async def gerar_recomendacao(
                self, *, contexto_empresa: str, base_normativa: str
            ) -> str:
                _ = (contexto_empresa, base_normativa)
                return "ok"

        s = Settings().model_copy(
            update={
                "llm_router_enabled": True,
                "llm_backend": "openai",
                "openai_chat_model": "gpt-4o-mini",
            }
        )
        router = LlmGatewayRouter(s, llm_service=_StubLlm())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.CLASSIFICACAO_RESPOSTA,
            prompt_key="cls",
            input_data={"x": 1},
        )
        resp = await router.complete(req)
        assert resp.model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_backend_anthropic_reflecte_modelo_nas_metas(self) -> None:
        class _StubLlm:
            async def gerar_recomendacao(
                self, *, contexto_empresa: str, base_normativa: str
            ) -> str:
                _ = (contexto_empresa, base_normativa)
                return "ok"

        s = Settings().model_copy(
            update={
                "llm_router_enabled": True,
                "llm_backend": "anthropic",
                "anthropic_model": "claude-3-5-haiku-latest",
            }
        )
        router = LlmGatewayRouter(s, llm_service=_StubLlm())
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.CLASSIFICACAO_RESPOSTA,
            prompt_key="cls",
            input_data={"x": 1},
        )
        resp = await router.complete(req)
        assert resp.model == "claude-3-5-haiku-latest"

    @pytest.mark.asyncio
    async def test_fake_adapter_explicito_prevale_sobre_llm_service(self) -> None:
        class _NuncaChamar:
            async def gerar_recomendacao(self, **kwargs: object) -> str:
                raise AssertionError("fake_adapter tem precedência")

        router = LlmGatewayRouter(
            _settings(),
            fake_adapter=FakeLlmAdapter(),
            llm_service=_NuncaChamar(),
        )
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr1",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="e",
            input_data={"score": 10.0},
        )
        resp = await router.complete(req)
        assert resp.provider == "fake"
