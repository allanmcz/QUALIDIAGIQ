"""Testes de ListarRetificacoesDiagnostico."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.application.use_cases.listar_retificacoes_diagnostico import (
    ComandoListarRetificacoesDiagnostico,
    ListarRetificacoesDiagnostico,
)


@pytest.mark.asyncio
async def test_execute_delega_limite_cap_200() -> None:
    tenant_id = uuid.uuid4()
    did = uuid.uuid4()
    ret = AsyncMock()
    ret.listar_por_diagnostico = AsyncMock(return_value=[])

    uc = ListarRetificacoesDiagnostico(retificacao=ret)
    await uc.execute(
        ComandoListarRetificacoesDiagnostico(
            tenant_id=tenant_id,
            diagnostico_original_id=did,
            limit=999,
        )
    )
    ret.listar_por_diagnostico.assert_awaited_once_with(
        tenant_id=tenant_id,
        diagnostico_original_id=did,
        limit=200,
    )
