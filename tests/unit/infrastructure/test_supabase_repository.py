import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)


@pytest.fixture
def diagnostico_mock():
    empresa = EmpresaInfo(
        cnpj="12345678000199",
        razao_social="Mock LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="123",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    respondente = Respondente(email="teste@teste.com")
    return Diagnostico(tenant_id=uuid.uuid4(), empresa=empresa, respondente=respondente)


@pytest.mark.asyncio
async def test_deve_salvar_diagnostico_no_supabase(diagnostico_mock):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute = AsyncMock(return_value=None)

    repo = SupabaseDiagnosticoRepository(client=mock_client)

    await repo.salvar(diagnostico_mock)

    mock_client.table.assert_called_with("diagnosticos")
    mock_table.upsert.assert_called_once()
    mock_upsert.execute.assert_called_once()


@pytest.mark.asyncio
async def test_deve_buscar_diagnostico_por_id_no_supabase(diagnostico_mock):
    mock_client = MagicMock()

    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2

    repo = SupabaseDiagnosticoRepository(client=mock_client)
    payload_banco = repo._para_dict(diagnostico_mock)
    mock_eq2.execute = AsyncMock(return_value=MagicMock(data=[payload_banco]))

    resultado = await repo.buscar_por_id(diagnostico_mock.id, diagnostico_mock.tenant_id)

    assert resultado is not None
    assert resultado.id == diagnostico_mock.id
    assert resultado.empresa.cnpj == "12345678000199"


@pytest.mark.asyncio
async def test_deve_listar_por_tenant(diagnostico_mock):
    mock_client = MagicMock()

    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_limit = MagicMock()
    mock_offset = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.limit.return_value = mock_limit
    mock_limit.offset.return_value = mock_offset

    repo = SupabaseDiagnosticoRepository(client=mock_client)
    payload_banco = repo._para_dict(diagnostico_mock)
    mock_offset.execute = AsyncMock(return_value=MagicMock(data=[payload_banco, payload_banco]))

    resultados = await repo.listar_por_tenant(diagnostico_mock.tenant_id)

    assert len(resultados) == 2
    assert resultados[0].id == diagnostico_mock.id
