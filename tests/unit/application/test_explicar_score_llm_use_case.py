"""Testes do ``ExplicarScoreLlmUseCase`` (ADR-022 Fase 3)."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

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
        assert out.text == "ok"
