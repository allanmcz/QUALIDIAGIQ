import uuid
from unittest.mock import MagicMock

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)


@pytest.fixture
def diagnostico_mock():
    empresa = EmpresaInfo(
        cnpj="12345678000195",
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
    mock_upsert.execute = MagicMock(return_value=None)

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
    mock_eq2.execute = MagicMock(return_value=MagicMock(data=[payload_banco]))

    resultado = await repo.buscar_por_id(diagnostico_mock.id, diagnostico_mock.tenant_id)

    assert resultado is not None
    assert resultado.id == diagnostico_mock.id
    assert resultado.empresa.cnpj == "12345678000195"


@pytest.mark.asyncio
async def test_para_dict_inclui_campos_worm_quando_evidencia_registrada(diagnostico_mock):
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
        score_por_dimensao={
            Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
        },
    )
    diagnostico_mock.finalizar(score_geral=70.0)
    diagnostico_mock.registrar_score_completo_para_evidencia(sc)

    repo = SupabaseDiagnosticoRepository(client=MagicMock())
    payload = repo._para_dict(diagnostico_mock)

    assert payload["hash_sha256"] == diagnostico_mock.hash_evidencia
    assert payload["hash_sha256"] is not None
    assert payload["score_completo"] == sc.para_dict_serializavel()
    assert payload["versao_otimista"] == 1
    assert payload["locale_relatorio"] == "pt-BR"
    assert payload["empresa_faixa_faturamento"] is None


@pytest.mark.asyncio
async def test_para_dict_serializa_faixa_faturamento_quando_informada(diagnostico_mock):
    diagnostico_mock.empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Mock LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
        faixa_faturamento=FaixaFaturamentoDeclarada.ACIMA_500_MI,
    )
    repo = SupabaseDiagnosticoRepository(client=MagicMock())
    payload = repo._para_dict(diagnostico_mock)
    assert payload["empresa_faixa_faturamento"] == "acima_500_mi"


@pytest.mark.asyncio
async def test_deve_listar_por_tenant(diagnostico_mock):
    mock_client = MagicMock()

    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    mock_limit = MagicMock()
    mock_offset = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order
    mock_order.limit.return_value = mock_limit
    mock_limit.offset.return_value = mock_offset

    repo = SupabaseDiagnosticoRepository(client=mock_client)
    payload_banco = repo._para_dict(diagnostico_mock)
    mock_offset.execute = MagicMock(return_value=MagicMock(data=[payload_banco, payload_banco]))

    resultados = await repo.listar_por_tenant(diagnostico_mock.tenant_id)

    assert len(resultados) == 2
    assert resultados[0].id == diagnostico_mock.id


@pytest.mark.asyncio
async def test_atualizar_relatorio_pdf_com_versao_retorna_entidade(diagnostico_mock):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_eq3 = MagicMock()
    mock_select = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.eq.return_value = mock_eq3
    mock_eq3.select.return_value = mock_select

    repo = SupabaseDiagnosticoRepository(client=mock_client)
    diagnostico_mock.finalizar(score_geral=80.0)
    diagnostico_mock.anexar_relatorio("https://bucket/rel.pdf")
    payload_pos_update = repo._para_dict(diagnostico_mock)
    payload_pos_update["versao_otimista"] = 2
    mock_select.execute = MagicMock(return_value=MagicMock(data=[payload_pos_update]))

    out = await repo.atualizar_relatorio_pdf_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        "https://bucket/rel.pdf",
        versao_esperada=1,
    )

    assert out is not None
    assert out.relatorio_pdf_url == "https://bucket/rel.pdf"
    assert out.versao_otimista == 2
    mock_table.update.assert_called_once()


@pytest.mark.asyncio
async def test_atualizar_relatorio_pdf_com_versao_none_quando_sem_linha(diagnostico_mock):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_eq3 = MagicMock()
    mock_select = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.eq.return_value = mock_eq3
    mock_eq3.select.return_value = mock_select
    mock_select.execute = MagicMock(return_value=MagicMock(data=[]))

    repo = SupabaseDiagnosticoRepository(client=mock_client)

    out = await repo.atualizar_relatorio_pdf_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        "https://bucket/rel.pdf",
        versao_esperada=9,
    )

    assert out is None


@pytest.mark.asyncio
async def test_atualizar_checklist_m12_com_versao_retorna_entidade(diagnostico_mock):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_eq3 = MagicMock()
    mock_select = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.eq.return_value = mock_eq3
    mock_eq3.select.return_value = mock_select

    repo = SupabaseDiagnosticoRepository(client=mock_client)
    diagnostico_mock.finalizar(score_geral=80.0)
    diagnostico_mock.definir_checklist_m12_autoconf([True] + [False] * 9)
    payload_pos_update = repo._para_dict(diagnostico_mock)
    payload_pos_update["versao_otimista"] = 2
    mock_select.execute = MagicMock(return_value=MagicMock(data=[payload_pos_update]))

    out = await repo.atualizar_checklist_m12_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        [True] + [False] * 9,
        versao_esperada=1,
    )

    assert out is not None
    assert out.checklist_m12_estado == [True] + [False] * 9
    assert out.versao_otimista == 2
    mock_table.update.assert_called_once()


@pytest.mark.asyncio
async def test_atualizar_checklist_m12_com_versao_none_quando_sem_linha(diagnostico_mock):
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_eq3 = MagicMock()
    mock_select = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.eq.return_value = mock_eq3
    mock_eq3.select.return_value = mock_select
    mock_select.execute = MagicMock(return_value=MagicMock(data=[]))

    repo = SupabaseDiagnosticoRepository(client=mock_client)

    out = await repo.atualizar_checklist_m12_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        [False] * 10,
        versao_esperada=9,
    )

    assert out is None
