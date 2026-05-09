"""Testes — adaptador em memória para vinculação de leads self-service (CI / Playwright)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.infrastructure.diagnosticos.memoria_lead_diagnostico_vinculo import (
    MemoriaLeadDiagnosticoVinculoAdapter,
)


@pytest.mark.asyncio
async def test_tenant_self_service_diferente_retorna_vazio_sem_chamar_repo() -> None:
    repo = MagicMock()
    repo.vincular_leads_self_service_em_memoria = MagicMock(return_value=[uuid4()])
    ss = uuid4()
    ad = MemoriaLeadDiagnosticoVinculoAdapter(repo, tenant_self_service=ss)
    dest = uuid4()
    out = await ad.vincular_gratuitos_self_service_para_tenant(
        email_admin_normalizado="admin@exemplo.com.br",
        tenant_destino=dest,
        tenant_self_service=uuid4(),
    )
    assert out == []
    repo.vincular_leads_self_service_em_memoria.assert_not_called()


@pytest.mark.asyncio
async def test_delega_ao_repositorio_quando_tenant_confere() -> None:
    repo = MagicMock()
    expected = [uuid4(), uuid4()]
    repo.vincular_leads_self_service_em_memoria.return_value = expected
    ss = uuid4()
    dest = uuid4()
    ad = MemoriaLeadDiagnosticoVinculoAdapter(repo, tenant_self_service=ss)
    email = "lead@dominio.com.br"
    out = await ad.vincular_gratuitos_self_service_para_tenant(
        email_admin_normalizado=email,
        tenant_destino=dest,
        tenant_self_service=ss,
    )
    assert out == expected
    repo.vincular_leads_self_service_em_memoria.assert_called_once_with(
        tenant_self_service=ss,
        tenant_destino=dest,
        email_admin_normalizado=email,
    )
