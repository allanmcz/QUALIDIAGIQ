"""Testes do caso de uso VincularDiagnosticosLeadSelfService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    ComandoVincularDiagnosticosLeadSelfService,
    VincularDiagnosticosLeadSelfService,
)


class TestVincularDiagnosticosLeadSelfService:
    """Delegação ao port de vinculação."""

    @pytest.mark.asyncio
    async def test_execute_retorna_ids_do_port(self) -> None:
        port = MagicMock()
        port.vincular_gratuitos_self_service_para_tenant = AsyncMock(
            return_value=[uuid4(), uuid4()]
        )
        uc = VincularDiagnosticosLeadSelfService(vinculo=port)
        tid = UUID("44444444-4444-4444-8444-444444444444")
        dest = UUID("55555555-5555-4555-8555-555555555555")
        cmd = ComandoVincularDiagnosticosLeadSelfService(
            email_admin_normalizado="a@b.com",
            tenant_destino=dest,
            tenant_self_service=tid,
        )
        out = await uc.execute(cmd)
        assert len(out) == 2
        port.vincular_gratuitos_self_service_para_tenant.assert_awaited_once_with(
            email_admin_normalizado="a@b.com",
            tenant_destino=dest,
            tenant_self_service=tid,
        )
