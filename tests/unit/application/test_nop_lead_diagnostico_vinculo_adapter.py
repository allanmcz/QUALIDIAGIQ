"""Testes do adaptador NOP de vinculação lead self-service → tenant painel."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.ports.lead_diagnostico_vinculo_port import (
    NopLeadDiagnosticoVinculoAdapter,
)


class TestNopLeadDiagnosticoVinculoAdapter:
    """Garante que o NOP não executa escrita quando não há `DATABASE_URL` sync."""

    @pytest.mark.asyncio
    async def test_vincular_gratuitos_retorna_lista_vazia(self) -> None:
        """
        Sem backend de vinculação, a chamada deve ser idempotente e devolver lista vazia.
        """
        ad = NopLeadDiagnosticoVinculoAdapter()
        tenant_destino = uuid4()
        tenant_self_service = uuid4()
        out = await ad.vincular_gratuitos_self_service_para_tenant(
            email_admin_normalizado="admin@exemplo.com.br",
            tenant_destino=tenant_destino,
            tenant_self_service=tenant_self_service,
        )
        assert out == []
