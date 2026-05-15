"""Testes do ``LlmServiceGatewayCompleter`` (Fase 2 ADR-022)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.domain.value_objects.evidence_ref import EvidenceRef
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.infrastructure.llm.adapters.llm_service_gateway_completer import LlmServiceGatewayCompleter


class TestLlmServiceGatewayCompleter:
    """Delega ao porto ``LlmServicePort`` sem expor SDK."""

    @pytest.mark.asyncio
    async def test_relatorio_usa_contexto_executivo_e_base_normativa(self) -> None:
        llm = AsyncMock()
        llm.gerar_recomendacao = AsyncMock(return_value="Recomendação sintética.")
        comp = LlmServiceGatewayCompleter(llm)
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.RELATORIO_EXECUTIVO,
            prompt_key="rel",
            input_data={
                "contexto_executivo": "Empresa X em transição.",
                "base_normativa": "Trecho LC 214/2025 art. 1º",
            },
        )
        out = await comp.complete(req)
        assert out == "Recomendação sintética."
        kwargs = llm.gerar_recomendacao.call_args.kwargs
        assert kwargs["contexto_empresa"] == "Empresa X em transição."
        assert "LC 214/2025 art. 1º" in kwargs["base_normativa"]
        assert "EC 132/2023" in kwargs["base_normativa"]

    @pytest.mark.asyncio
    async def test_rag_com_evidencias_serializa_dispositivos(self) -> None:
        llm = AsyncMock()
        llm.gerar_recomendacao = AsyncMock(return_value="ok")
        comp = LlmServiceGatewayCompleter(llm)
        ev = EvidenceRef(fonte="Lexiq", titulo="T", dispositivo="LC 214/2025 art. 9º")
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={"nota": "revisão"},
            evidencias=(ev,),
        )
        await comp.complete(req)
        base = llm.gerar_recomendacao.call_args.kwargs["base_normativa"]
        assert "LC 214/2025 art. 9º" in base

    @pytest.mark.asyncio
    async def test_evidencia_com_url_inclui_na_base(self) -> None:
        llm = AsyncMock()
        llm.gerar_recomendacao = AsyncMock(return_value="ok")
        comp = LlmServiceGatewayCompleter(llm)
        ev = EvidenceRef(
            fonte="Lexiq",
            titulo="T",
            dispositivo="LC 214/2025 art. 2º",
            url="https://exemplo.invalido/doc",
        )
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.ANALISE_NORMATIVA_RAG,
            prompt_key="rag",
            input_data={},
            evidencias=(ev,),
        )
        await comp.complete(req)
        base = llm.gerar_recomendacao.call_args.kwargs["base_normativa"]
        assert "https://exemplo.invalido/doc" in base

    @pytest.mark.asyncio
    async def test_sem_contexto_executivo_serializa_input(self) -> None:
        llm = AsyncMock()
        llm.gerar_recomendacao = AsyncMock(return_value="ok")
        comp = LlmServiceGatewayCompleter(llm)
        req = LlmGatewayRequest(
            tenant_id="t1",
            trace_id="tr",
            task_type=LlmTaskType.CLASSIFICACAO_RESPOSTA,
            prompt_key="cls",
            input_data={"resposta": "talvez"},
        )
        await comp.complete(req)
        ctx = llm.gerar_recomendacao.call_args.kwargs["contexto_empresa"]
        assert "tarefa:" in ctx
        assert "resposta: talvez" in ctx
