"""Cobertura residual do ``SupabaseDiagnosticoRepository`` (mocks PostgREST)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)


@pytest.fixture
def diagnostico_mock() -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Mock LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    respondente = Respondente(email="teste@teste.com")
    return Diagnostico(tenant_id=uuid4(), empresa=empresa, respondente=respondente)


def _repo_tabelas_backfill(
    *,
    plano_hit: list[dict],
    diag_payload: dict | list | None,
) -> SupabaseDiagnosticoRepository:
    mock_client = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "diagnostico_plano_acao":
            m.select.return_value.eq.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
                data=plano_hit
            )
        elif name == "diagnosticos":
            m.select.return_value.eq.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
                data=diag_payload
            )
        else:
            raise AssertionError(f"tabela inesperada: {name}")
        return m

    mock_client.table.side_effect = table
    return SupabaseDiagnosticoRepository(mock_client)


@pytest.mark.asyncio
async def test_buscar_por_id_retorna_none_quando_sem_linhas(diagnostico_mock: Diagnostico) -> None:
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute = MagicMock(return_value=MagicMock(data=[]))

    repo = SupabaseDiagnosticoRepository(mock_client)
    assert await repo.buscar_por_id(diagnostico_mock.id, diagnostico_mock.tenant_id) is None


@pytest.mark.asyncio
async def test_atualizar_quadro_implantacao_com_versao_ok_e_none(
    diagnostico_mock: Diagnostico,
) -> None:
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

    repo = SupabaseDiagnosticoRepository(mock_client)
    blob = {"f0_a0": {"prazo_meta": "", "comentarios": [], "descricao_personalizada": ""}}
    payload_ok = repo._para_dict(diagnostico_mock)
    payload_ok["versao_otimista"] = 2
    mock_select.execute = MagicMock(return_value=MagicMock(data=[payload_ok]))

    out = await repo.atualizar_quadro_implantacao_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        blob,
        versao_esperada=1,
    )
    assert out is not None

    mock_select.execute = MagicMock(return_value=MagicMock(data=[]))
    out_none = await repo.atualizar_quadro_implantacao_com_versao(
        diagnostico_mock.id,
        diagnostico_mock.tenant_id,
        blob,
        versao_esperada=9,
    )
    assert out_none is None


@pytest.mark.asyncio
async def test_salvar_e_materializar_plano_painel(diagnostico_mock: Diagnostico) -> None:
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )
    diagnostico_mock.finalizar(score_geral=70.0)
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute = MagicMock(return_value=None)

    plano = PlanoPainelSerializado(versao_plano=1, checklist=(), matriz_impacto=(), cronograma=())
    repo = SupabaseDiagnosticoRepository(mock_client)

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.materializar_plano_painel_supabase",
        return_value=plano,
    ) as mat_mock:
        out = await repo.salvar_e_materializar_plano_painel(
            diagnostico_mock,
            sc,
            historico_campos_empresa_cnpj=[("a", None, "b")],
            cnpj_consulta_id=uuid4(),
        )

    assert out is plano
    mat_mock.assert_called_once()
    mock_table.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_buscar_plano_painel_serializado(diagnostico_mock: Diagnostico) -> None:
    mock_client = MagicMock()
    repo = SupabaseDiagnosticoRepository(mock_client)
    plano = PlanoPainelSerializado(versao_plano=1, checklist=(), matriz_impacto=(), cronograma=())

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.buscar_plano_painel_serializado_supabase",
        return_value=None,
    ):
        assert (
            await repo.buscar_plano_painel_serializado(
                diagnostico_mock.id, diagnostico_mock.tenant_id
            )
            is None
        )

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.buscar_plano_painel_serializado_supabase",
        return_value=plano,
    ):
        assert (
            await repo.buscar_plano_painel_serializado(
                diagnostico_mock.id, diagnostico_mock.tenant_id
            )
            is plano
        )


def test_materializar_backfill_retorna_none_quando_plano_ja_existe(
    diagnostico_mock: Diagnostico,
) -> None:
    repo = _repo_tabelas_backfill(plano_hit=[{"id": "1"}], diag_payload=None)
    assert (
        repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id) is None
    )


def test_materializar_backfill_retorna_none_quando_diagnostico_nao_dict(
    diagnostico_mock: Diagnostico,
) -> None:
    repo = _repo_tabelas_backfill(plano_hit=[], diag_payload=[])
    assert (
        repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id) is None
    )


def test_materializar_backfill_retorna_none_quando_nao_finalizado(
    diagnostico_mock: Diagnostico,
) -> None:
    repo_plain = SupabaseDiagnosticoRepository(MagicMock())
    row = repo_plain._para_dict(diagnostico_mock)
    row["status"] = StatusDiagnostico.EM_ANDAMENTO.value
    repo = _repo_tabelas_backfill(plano_hit=[], diag_payload=row)
    assert (
        repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id) is None
    )


def test_materializar_backfill_retorna_none_quando_score_completo_invalido(
    diagnostico_mock: Diagnostico,
) -> None:
    repo_plain = SupabaseDiagnosticoRepository(MagicMock())
    diagnostico_mock.finalizar(score_geral=70.0)
    row = repo_plain._para_dict(diagnostico_mock)
    row["status"] = StatusDiagnostico.FINALIZADO.value
    row["score_completo"] = "nao-dict"
    repo = _repo_tabelas_backfill(plano_hit=[], diag_payload=row)
    assert (
        repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id) is None
    )


def test_materializar_backfill_retorna_none_quando_desde_dict_falha(
    diagnostico_mock: Diagnostico,
) -> None:
    repo_plain = SupabaseDiagnosticoRepository(MagicMock())
    diagnostico_mock.finalizar(score_geral=70.0)
    row = repo_plain._para_dict(diagnostico_mock)
    row["status"] = StatusDiagnostico.FINALIZADO.value
    row["score_completo"] = {
        "score_geral": {"valor": 1.0, "peso_total_aplicado": 1.0},
        "score_por_dimensao": {},
    }
    repo = _repo_tabelas_backfill(plano_hit=[], diag_payload=row)
    assert (
        repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id) is None
    )


def test_materializar_backfill_sucesso_chama_materializar(diagnostico_mock: Diagnostico) -> None:
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )
    repo_plain = SupabaseDiagnosticoRepository(MagicMock())
    diagnostico_mock.finalizar(score_geral=70.0)
    diagnostico_mock.registrar_score_completo_para_evidencia(sc)
    row = repo_plain._para_dict(diagnostico_mock)
    row["status"] = StatusDiagnostico.FINALIZADO.value
    repo = _repo_tabelas_backfill(plano_hit=[], diag_payload=row)
    esperado = PlanoPainelSerializado(1, (), (), ())

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.materializar_plano_painel_supabase",
        return_value=esperado,
    ) as mat_mock:
        out = repo._materializar_backfill_thread(diagnostico_mock.id, diagnostico_mock.tenant_id)

    assert out is esperado
    mat_mock.assert_called_once()


@pytest.mark.asyncio
async def test_materializar_plano_painel_idempotente_backfill_async(
    diagnostico_mock: Diagnostico,
) -> None:
    repo = _repo_tabelas_backfill(plano_hit=[{"id": "x"}], diag_payload=None)

    async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
        return fn(*args, **kwargs)

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.asyncio.to_thread",
        side_effect=run_imediato,
    ):
        assert (
            await repo.materializar_plano_painel_idempotente_backfill(
                diagnostico_mock.id, diagnostico_mock.tenant_id
            )
            is None
        )


@pytest.mark.asyncio
async def test_inserir_e_atualizar_subtarefa_plano(diagnostico_mock: Diagnostico) -> None:
    mock_client = MagicMock()
    repo = SupabaseDiagnosticoRepository(mock_client)
    tid, did, pid, sid = uuid4(), diagnostico_mock.id, uuid4(), uuid4()

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.inserir_subtarefa_supabase",
        return_value={"id": "sub"},
    ) as ins:
        out = await repo.inserir_subtarefa_plano(tid, did, pid, "Título", ordem=1)
    assert out == {"id": "sub"}
    ins.assert_called_once()

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.atualizar_subtarefa_supabase",
        return_value={"ok": True},
    ) as upd:
        out2 = await repo.atualizar_subtarefa_plano(
            tid, did, sid, titulo="Novo", status="aberta", prazo=None, comentarios=None, ordem=2
        )
    assert out2 == {"ok": True}
    upd.assert_called_once()


@pytest.mark.asyncio
async def test_atualizar_explicacao_score_llm_sucesso_e_nao_encontrado(
    diagnostico_mock: Diagnostico,
) -> None:
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq_id = MagicMock()
    mock_eq_tenant = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq_id
    mock_eq_id.eq.return_value = mock_eq_tenant
    repo = SupabaseDiagnosticoRepository(mock_client)
    snap = {"text": "ok"}

    mock_resp = MagicMock()
    mock_resp.data = [{"id": str(diagnostico_mock.id)}]
    mock_eq_tenant.execute = MagicMock(return_value=mock_resp)

    with patch(
        "src.infrastructure.repositories.supabase_diagnostico_repository.asyncio.to_thread",
        side_effect=lambda fn: fn(),
    ):
        await repo.atualizar_explicacao_score_llm(
            diagnostico_mock.id, diagnostico_mock.tenant_id, snap
        )

    mock_table.update.assert_called_once_with({"explicacao_score_llm": snap})

    mock_resp_vazio = MagicMock()
    mock_resp_vazio.data = []
    mock_eq_tenant.execute = MagicMock(return_value=mock_resp_vazio)
    with (
        patch(
            "src.infrastructure.repositories.supabase_diagnostico_repository.asyncio.to_thread",
            side_effect=lambda fn: fn(),
        ),
        pytest.raises(ValueError, match="não encontrado"),
    ):
        await repo.atualizar_explicacao_score_llm(
            diagnostico_mock.id, diagnostico_mock.tenant_id, snap
        )


def test_para_entity_score_completo_malformado_fica_none(diagnostico_mock: Diagnostico) -> None:
    repo = SupabaseDiagnosticoRepository(MagicMock())
    base = repo._para_dict(diagnostico_mock)
    base["score_completo"] = {"invalido": True}
    ent = repo._para_entity(base)
    assert ent.score_completo_snapshot is None


def test_para_entity_campos_opcionais_e_faixa_invalida(diagnostico_mock: Diagnostico) -> None:
    repo = SupabaseDiagnosticoRepository(MagicMock())
    base = repo._para_dict(diagnostico_mock)
    base["aceite_termos_privacidade_em"] = "2026-01-15T12:00:00+00:00"
    base["locale_relatorio"] = "en-US"
    base["empresa_faixa_faturamento"] = "valor_inexistente_no_enum"
    ent = repo._para_entity(base)
    assert ent.aceite_termos_privacidade_em is not None
    assert ent.locale_relatorio == "en-US"
    assert ent.empresa.faixa_faturamento is None


def test_para_entity_quadro_com_comentario_legado(diagnostico_mock: Diagnostico) -> None:
    repo = SupabaseDiagnosticoRepository(MagicMock())
    base = repo._para_dict(diagnostico_mock)
    base["quadro_implantacao_anotacoes"] = {
        "f1_a0": {
            "prazo_meta": "",
            "comentarios": [],
            "comentario": "  nota única  ",
            "descricao_personalizada": "x",
        }
    }
    ent = repo._para_entity(base)
    assert ent.quadro_implantacao_anotacoes is not None
    assert ent.quadro_implantacao_anotacoes["f1_a0"]["comentarios"] == ["nota única"]


def test_para_entity_quadro_cobre_ramos_parse(diagnostico_mock: Diagnostico) -> None:
    """Exercita ramos de ``_para_entity`` no parse de ``quadro_implantacao_anotacoes``."""
    repo = SupabaseDiagnosticoRepository(MagicMock())
    base = repo._para_dict(diagnostico_mock)
    base["quadro_implantacao_anotacoes"] = {
        "ignorado_nao_dict": "valor_escalar",
        "lista_com_itens": {
            "prazo_meta": " p1 ",
            "comentarios": [" a ", "", "  b  "],
            "descricao_personalizada": "dp",
        },
        "lista_vazia_mais_legado": {
            "prazo_meta": "",
            "comentarios": ["  ", ""],
            "comentario": " só legado ",
        },
        "comentarios_nao_lista": {
            "comentarios": "não é lista",
            "comentario": "fallback",
        },
        "sem_descricao_personalizada": {
            "prazo_meta": "z",
            "comentarios": ["ok"],
            "descricao_personalizada": "   ",
        },
        "sem_comentarios_nem_legado": {
            "prazo_meta": "w",
            "comentarios": [],
            "comentario": "   ",
        },
    }
    ent = repo._para_entity(base)
    q = ent.quadro_implantacao_anotacoes
    assert q is not None
    assert "ignorado_nao_dict" not in q
    assert q["lista_com_itens"]["prazo_meta"] == "p1"
    assert q["lista_com_itens"]["comentarios"] == ["a", "b"]
    assert q["lista_com_itens"]["descricao_personalizada"] == "dp"
    assert q["lista_vazia_mais_legado"]["comentarios"] == ["só legado"]
    assert q["comentarios_nao_lista"]["comentarios"] == ["fallback"]
    assert "descricao_personalizada" not in q["sem_descricao_personalizada"]
    assert q["sem_comentarios_nem_legado"]["comentarios"] == []


@pytest.mark.asyncio
async def test_registrar_e_listar_explicacao_historico_memoria(
    diagnostico_mock: Diagnostico,
) -> None:
    """Histórico LLM em memória no adapter Supabase (MVP sem tabela dedicada)."""
    repo = SupabaseDiagnosticoRepository(MagicMock())
    tid = diagnostico_mock.tenant_id
    did = diagnostico_mock.id
    snap = {"text": "hist", "provider": "fake", "model": "m", "policy_version": "v"}
    await repo.registrar_explicacao_score_llm_historico(
        did, tid, snap, actor_user_id=None, trace_id="t1"
    )
    rows = await repo.listar_explicacao_score_llm_historico(did, tid)
    assert rows[0]["text"] == "hist"

    await repo.registrar_explicacao_score_llm_historico(
        did, tid, {"text": "sem trace"}, actor_user_id=None, trace_id=None
    )
    rows2 = await repo.listar_explicacao_score_llm_historico(did, tid)
    assert rows2[0]["text"] == "sem trace"
    assert "trace_id" not in rows2[0] or rows2[0].get("trace_id") is None
