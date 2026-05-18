"""Testes do ``ExplicarScoreLlmUseCase`` (ADR-022 Fase 3)."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo
from src.application.services.explicacao_score_rag import MENSAGEM_BASE_NORMATIVA_INSUFICIENTE
from src.application.use_cases.explicar_score_llm_use_case import (
    ComandoExplicarScoreLlm,
    ExplicarScoreLlmUseCase,
)
from src.domain.ports.llm_gateway import LlmGatewayResponse
from src.domain.value_objects.llm_task_type import LlmTaskType


class TestExplicarScoreLlmUseCase:
    """Orquestra pedido canónico ao gateway."""

    @pytest.mark.asyncio
    async def test_delega_complete_com_explicacao_score(self) -> None:
        gw = AsyncMock()
        gw.complete = AsyncMock(
            return_value=LlmGatewayResponse(
                text="ok",
                provider="fake",
                model="fake-llm",
                policy_version="2026-05-15-v1",
            )
        )
        uc = ExplicarScoreLlmUseCase(gateway=gw)
        tid = uuid4()
        out = await uc.execute(
            ComandoExplicarScoreLlm(tenant_id=tid, trace_id="tr-1", score_geral=72.5)
        )
        gw.complete.assert_awaited_once()
        req = gw.complete.call_args[0][0]
        assert req.task_type == LlmTaskType.EXPLICACAO_SCORE
        assert req.input_data["score_geral"] == 72.5
        assert req.tenant_id == str(tid)
        assert req.idempotency_key is None
        assert out.text == "ok"

    @pytest.mark.asyncio
    async def test_repasse_idempotency_key_ao_gateway(self) -> None:
        gw = AsyncMock()
        gw.complete = AsyncMock(
            return_value=LlmGatewayResponse(
                text="x",
                provider="fake",
                model="m",
                policy_version="v",
            )
        )
        uc = ExplicarScoreLlmUseCase(gateway=gw)
        tid = uuid4()
        await uc.execute(
            ComandoExplicarScoreLlm(
                tenant_id=tid,
                trace_id="tr-2",
                score_geral=50.0,
                idempotency_key="chave-http-1",
            )
        )
        req = gw.complete.call_args[0][0]
        assert req.idempotency_key == "chave-http-1"

    @pytest.mark.asyncio
    async def test_campos_extras_mesclados_em_input_data(self) -> None:
        gw = AsyncMock()
        gw.complete = AsyncMock(
            return_value=LlmGatewayResponse(
                text="x",
                provider="fake",
                model="m",
                policy_version="v",
            )
        )
        uc = ExplicarScoreLlmUseCase(gateway=gw)
        tid = uuid4()
        await uc.execute(
            ComandoExplicarScoreLlm(
                tenant_id=tid,
                trace_id="tr-3",
                score_geral=55.0,
                campos_extras={
                    "score_por_dimensao": {"fiscal": 40.0},
                    "empresa_uf": "SP",
                },
            )
        )
        req = gw.complete.call_args[0][0]
        assert req.input_data["score_geral"] == 55.0
        assert req.input_data["score_por_dimensao"] == {"fiscal": 40.0}
        assert req.input_data["empresa_uf"] == "SP"

    @pytest.mark.asyncio
    async def test_rag_anexa_fontes_e_contexto_no_gateway(self) -> None:
        gw = AsyncMock()
        gw.complete = AsyncMock(
            return_value=LlmGatewayResponse(
                text="parecer ok",
                provider="fake",
                model="m",
                policy_version="v",
            )
        )
        port = AsyncMock()
        port.buscar_contexto = AsyncMock(
            return_value=[
                ChunkNormativo(
                    texto="MVP QualiDiagIQ reforma tributária.",
                    score=0.88,
                    fonte="PRD_BASE",
                    artigo="docs/refs/01_PRD_BASE.md",
                )
            ]
        )
        uc = ExplicarScoreLlmUseCase(
            gateway=gw,
            base_normativa_port=port,
            rag_similarity_threshold=0.5,
        )
        out = await uc.execute(
            ComandoExplicarScoreLlm(tenant_id=uuid4(), trace_id="tr-rag", score_geral=70.0)
        )
        req = gw.complete.call_args[0][0]
        assert "rag_contexto" in req.input_data
        assert req.input_data["rag_status"] == "com_fonte"
        assert len(req.evidencias) >= 1
        assert out.rag_status == "com_fonte"
        assert len(out.fontes_rag) == 1

    @pytest.mark.asyncio
    async def test_bloqueia_llm_quando_rag_base_insuficiente(self) -> None:
        gw = AsyncMock()
        port = AsyncMock(spec=BaseNormativaPort)
        port.buscar_contexto = AsyncMock(
            return_value=[
                ChunkNormativo(
                    texto="fraco",
                    score=0.1,
                    fonte="FONTE-020",
                    catalogo_id="FONTE-020",
                    classe="B",
                )
            ]
        )
        uc = ExplicarScoreLlmUseCase(gateway=gw, base_normativa_port=port, rag_similarity_threshold=0.65)
        out = await uc.execute(
            ComandoExplicarScoreLlm(tenant_id=uuid4(), trace_id="tr-block", score_geral=50.0)
        )
        gw.complete.assert_not_awaited()
        assert out.blocked_by_guardrail is True
        assert out.guardrail_reason == "rag_base_insuficiente"
        assert MENSAGEM_BASE_NORMATIVA_INSUFICIENTE in out.text
        assert out.rag_status == "base_insuficiente"
