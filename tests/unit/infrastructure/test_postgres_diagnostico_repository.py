"""Testes do ``PostgresDiagnosticoRepository`` com mock de ``psycopg2.connect``."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
    _explicacao_score_llm_de_row,
    _inserir_historico_cnpj_cur,
    _materializar_plano_backfill_sync,
    _patch_explicacao_score_llm_sync,
    _patch_m12_sync,
    _patch_quadro_sync,
    _patch_relatorio_sync,
    _quadro_anotacoes_de_row,
    _row_dict_para_entity,
    _salvar_e_materializar_plano_sync,
)


def _diag_minimo() -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Empresa Teste",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="6201500",
        uf="SP",
        setor_macro=SetorMacro.SERVICOS,
    )
    return Diagnostico(
        tenant_id=uuid4(),
        empresa=emp,
        respondente=Respondente(email="a@b.com", nome="Nome QA"),
        plano=PlanoDiagnostico.GRATUITO,
    )


def _mock_conn_cursor(mock_cursor: MagicMock) -> MagicMock:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cm
    return mock_conn


def _row_minima(did, tid) -> dict:
    return {
        "id": str(did),
        "tenant_id": str(tid),
        "respondente_email": "a@b.com",
        "respondente_nome": "Nome",
        "respondente_cargo": None,
        "respondente_telefone": None,
        "respondente_ip_origem": None,
        "empresa_cnpj": "12345678000195",
        "empresa_razao_social": "Empresa",
        "empresa_porte": "micro",
        "empresa_regime": "simples_nacional",
        "empresa_cnae": "6201500",
        "empresa_uf": "SP",
        "empresa_setor_macro": "servicos",
        "empresa_faixa_faturamento": None,
        "status": "finalizado",
        "plano": "gratuito",
        "score_geral": 50.0,
        "relatorio_pdf_url": None,
        "criado_em": datetime.now(UTC),
        "finalizado_em": datetime.now(UTC),
        "hash_sha256": None,
        "score_completo": None,
        "versao_otimista": 1,
        "checklist_m12_estado": None,
        "quadro_implantacao_anotacoes": None,
        "aceite_termos_privacidade_em": None,
        "locale_relatorio": "pt-BR",
        "versao_plano": 1,
    }


@pytest.mark.asyncio
class TestPostgresDiagnosticoRepository:
    """I/O simulado — sem Postgres real."""

    async def test_salvar_commita(self) -> None:
        mock_cursor = MagicMock()
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.salvar(_diag_minimo())
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    async def test_salvar_rollback_em_erro(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = RuntimeError("db down")
        mock_conn = _mock_conn_cursor(mock_cursor)
        with (
            patch(
                "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
                return_value=mock_conn,
            ),
            pytest.raises(RuntimeError, match="db down"),
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.salvar(_diag_minimo())
        mock_conn.rollback.assert_called_once()

    async def test_atualizar_explicacao_score_llm_async(self) -> None:
        did, tid = uuid4(), uuid4()
        snap = {"text": "async"}
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository._patch_explicacao_score_llm_sync"
        ) as mock_patch:
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.atualizar_explicacao_score_llm(did, tid, snap)
        mock_patch.assert_called_once_with("postgresql://u:p@localhost:1/db", did, tid, snap)

    async def test_registrar_explicacao_historico_async(self) -> None:
        did, tid, uid = uuid4(), uuid4(), uuid4()
        snap = {"text": "h"}
        with patch(
            "src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync.inserir_explicacao_score_llm_historico_sync"
        ) as mock_ins:
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.registrar_explicacao_score_llm_historico(
                did, tid, snap, actor_user_id=uid, trace_id="tr"
            )
        mock_ins.assert_called_once()

    async def test_listar_explicacao_historico_async(self) -> None:
        did, tid = uuid4(), uuid4()
        with patch(
            "src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync.listar_explicacao_score_llm_historico_sync",
            return_value=[{"text": "x"}],
        ) as mock_lst:
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.listar_explicacao_score_llm_historico(did, tid, limit=3)
        assert out[0]["text"] == "x"
        mock_lst.assert_called_once()

    async def test_buscar_por_id_retorna_entidade(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _row_minima(did, tid)
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.buscar_por_id(did, tid)
        assert out is not None
        assert out.id == did
        assert out.status == StatusDiagnostico.FINALIZADO

    async def test_buscar_por_id_none(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.buscar_por_id(uuid4(), uuid4())
        assert out is None

    async def test_listar_por_tenant(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [_row_minima(did, tid)]
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            rows = await repo.listar_por_tenant(tid, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0].id == did

    async def test_listar_por_tenant_filtra_empresa_cnpj(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [_row_minima(did, tid)]
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            rows = await repo.listar_por_tenant(
                tid, limit=10, offset=0, empresa_cnpj="12345678000195"
            )
        assert len(rows) == 1
        sql_executado = mock_cursor.execute.call_args[0][0]
        assert "empresa_cnpj = %s" in sql_executado

    async def test_atualizar_relatorio_retorna_none_se_zero_linhas(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_relatorio_pdf_com_versao(
                uuid4(), uuid4(), "https://x/p.pdf", versao_esperada=1
            )
        assert out is None

    async def test_atualizar_relatorio_retorna_entidade(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _row_minima(did, tid)
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_relatorio_pdf_com_versao(
                did, tid, "https://x/p.pdf", versao_esperada=1
            )
        assert out is not None
        assert out.id == did

    async def test_atualizar_quadro_implantacao_none_quando_conflito(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_quadro_implantacao_com_versao(
                did, tid, {"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}}, versao_esperada=9
            )
        assert out is None

    async def test_atualizar_quadro_implantacao(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        row = _row_minima(did, tid)
        row["quadro_implantacao_anotacoes"] = {"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}}
        mock_cursor.fetchone.return_value = row
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_quadro_implantacao_com_versao(
                did, tid, {"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}}, versao_esperada=1
            )
        assert out is not None
        assert out.quadro_implantacao_anotacoes == {
            "f0_a0": {"comentarios": ["x"], "prazo_meta": ""}
        }

    async def test_atualizar_m12_none_quando_conflito(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_checklist_m12_com_versao(
                did, tid, [1] * 10, versao_esperada=99
            )
        assert out is None

    async def test_atualizar_m12(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        row = _row_minima(did, tid)
        row["checklist_m12_estado"] = [5] * 10
        mock_cursor.fetchone.return_value = row
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_checklist_m12_com_versao(
                did, tid, [5] * 10, versao_esperada=1
            )
        assert out is not None
        assert out.checklist_m12_estado == [5] * 10

    async def test_metodos_proxy_usam_asyncio_to_thread(self) -> None:
        repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
        d = _diag_minimo()
        sc = _score_completo_snapshot()
        did, tid = uuid4(), uuid4()

        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.asyncio.to_thread",
            new_callable=AsyncMock,
        ) as mock_to_thread:
            mock_to_thread.return_value = None
            await repo.salvar_e_materializar_plano_painel(d, sc)
            await repo.buscar_plano_painel_serializado(did, tid)
            await repo.materializar_plano_painel_idempotente_backfill(did, tid)
            await repo.inserir_subtarefa_plano(tid, did, uuid4(), "sub", 1)
            await repo.atualizar_subtarefa_plano(tid, did, uuid4(), titulo="x")

        assert mock_to_thread.await_count == 5


def _score_completo_snapshot():
    return ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )


def test_salvar_e_materializar_plano_sync_fluxo_feliz() -> None:
    d = _diag_minimo()
    d.finalizar(70.0)
    sc = _score_completo_snapshot()
    mock_cursor = MagicMock()
    mock_conn = _mock_conn_cursor(mock_cursor)
    plano_serializado = PlanoPainelSerializado(
        versao_plano=1, checklist=(), matriz_impacto=(), cronograma=()
    )
    deriv = MagicMock()
    deriv.serializado_http = plano_serializado

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.derivar_plano_painel_materializado",
            return_value=deriv,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.materializar_plano_em_conexao"
        ) as mock_mat,
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.buscar_plano_painel_serializado_sync",
            return_value=plano_serializado,
        ),
    ):
        out = _salvar_e_materializar_plano_sync("postgresql://u:p@localhost:1/db", d, sc)

    assert out == plano_serializado
    mock_conn.commit.assert_called_once()
    mock_mat.assert_called_once()
    mock_conn.close.assert_called_once()


def test_salvar_e_materializar_plano_sync_rollback_quando_materializar_falha() -> None:
    d = _diag_minimo()
    d.finalizar(70.0)
    sc = _score_completo_snapshot()
    mock_cursor = MagicMock()
    mock_conn = _mock_conn_cursor(mock_cursor)
    deriv = MagicMock()

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.derivar_plano_painel_materializado",
            return_value=deriv,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.materializar_plano_em_conexao",
            side_effect=RuntimeError("falha ao materializar"),
        ),
        pytest.raises(RuntimeError, match="materializar"),
    ):
        _salvar_e_materializar_plano_sync("postgresql://u:p@localhost:1/db", d, sc)

    mock_conn.rollback.assert_called_once()
    mock_conn.close.assert_called_once()


def test_salvar_e_materializar_plano_sync_rollback_em_erro() -> None:
    d = _diag_minimo()
    d.finalizar(70.0)
    sc = _score_completo_snapshot()
    mock_cursor = MagicMock()
    mock_conn = _mock_conn_cursor(mock_cursor)

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.derivar_plano_painel_materializado",
            side_effect=RuntimeError("falha ao derivar"),
        ),
        pytest.raises(RuntimeError, match="falha ao derivar"),
    ):
        _salvar_e_materializar_plano_sync("postgresql://u:p@localhost:1/db", d, sc)

    mock_conn.rollback.assert_not_called()


def test_materializar_plano_backfill_sync_retorna_none_quando_ja_existe() -> None:
    with patch(
        "src.infrastructure.repositories.postgres_diagnostico_repository.plano_materializado_existe_sync",
        return_value=True,
    ):
        out = _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", uuid4(), uuid4())
    assert out is None


def test_materializar_plano_backfill_sync_fluxos_de_nao_materializar() -> None:
    did, tid = uuid4(), uuid4()
    d = _diag_minimo()
    d.tenant_id = tid

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.plano_materializado_existe_sync",
            return_value=False,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository._buscar_sync",
            side_effect=[None, d, d],
        ),
    ):
        assert (
            _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", did, tid) is None
        )
        d.status = StatusDiagnostico.EM_ANDAMENTO
        assert (
            _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", did, tid) is None
        )
        d.status = StatusDiagnostico.FINALIZADO
        d.score_completo_snapshot = None
        assert (
            _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", did, tid) is None
        )


def test_materializar_plano_backfill_sync_materializa_quando_elegivel() -> None:
    did, tid = uuid4(), uuid4()
    d = _diag_minimo()
    d.tenant_id = tid
    d.finalizar(70.0)
    d.score_completo_snapshot = _score_completo_snapshot()
    mock_conn = MagicMock()
    mock_conn.autocommit = False
    deriv = MagicMock()
    plano_serializado = PlanoPainelSerializado(
        versao_plano=1, checklist=(), matriz_impacto=(), cronograma=()
    )

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.plano_materializado_existe_sync",
            return_value=False,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository._buscar_sync",
            return_value=d,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.derivar_plano_painel_materializado",
            return_value=deriv,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.materializar_plano_em_conexao"
        ) as mock_mat,
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.buscar_plano_painel_serializado_sync",
            return_value=plano_serializado,
        ),
    ):
        out = _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", did, tid)

    assert out == plano_serializado
    mock_mat.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def test_materializar_plano_backfill_sync_rollback_quando_materializar_falha() -> None:
    did, tid = uuid4(), uuid4()
    d = _diag_minimo()
    d.tenant_id = tid
    d.finalizar(70.0)
    d.score_completo_snapshot = _score_completo_snapshot()
    mock_conn = MagicMock()
    mock_conn.autocommit = False
    deriv = MagicMock()

    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.plano_materializado_existe_sync",
            return_value=False,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository._buscar_sync",
            return_value=d,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.derivar_plano_painel_materializado",
            return_value=deriv,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.materializar_plano_em_conexao",
            side_effect=RuntimeError("erro materializar backfill"),
        ),
        pytest.raises(RuntimeError, match="materializar backfill"),
    ):
        _materializar_plano_backfill_sync("postgresql://u:p@localhost:1/db", did, tid)

    mock_conn.rollback.assert_called_once()
    mock_conn.close.assert_called_once()


def test_inserir_historico_cnpj_cur_sem_itens_nao_chama_execute() -> None:
    cur = MagicMock()
    _inserir_historico_cnpj_cur(cur, uuid4(), uuid4(), [], None)
    cur.execute.assert_not_called()


def test_inserir_historico_cnpj_cur_grava_linhas() -> None:
    cur = MagicMock()
    tid, did, cq = uuid4(), uuid4(), uuid4()
    _inserir_historico_cnpj_cur(
        cur,
        tid,
        did,
        [("empresa_uf", "SP", "RJ")],
        cq,
    )
    cur.execute.assert_called_once()
    args = cur.execute.call_args[0][1]
    assert args[0] == str(tid)
    assert args[1] == str(did)
    assert args[2] == str(cq)


def test_explicacao_score_llm_de_row_dict_ou_none() -> None:
    assert _explicacao_score_llm_de_row({"explicacao_score_llm": {"text": "ok"}}) == {"text": "ok"}
    assert _explicacao_score_llm_de_row({"explicacao_score_llm": "nao-dict"}) is None
    assert _explicacao_score_llm_de_row({}) is None


def test_quadro_anotacoes_de_row_limpeza_e_legado() -> None:
    row = {
        "quadro_implantacao_anotacoes": {
            "ok": {
                "prazo_meta": " 2026-07-01 ",
                "comentarios": [" x ", "", "y"],
                "descricao_personalizada": "  desc ",
            },
            "legado": {"comentario": "  nota única  "},
            "so_brancos": {"prazo_meta": "", "comentarios": ["", "  "]},
            "ignorar": "nao-dict",
        }
    }
    out = _quadro_anotacoes_de_row(row)
    assert out is not None
    assert out["ok"]["comentarios"] == ["x", "y"]
    assert out["ok"]["descricao_personalizada"] == "desc"
    assert out["legado"]["comentarios"] == ["nota única"]
    assert out["so_brancos"]["comentarios"] == []


def test_row_dict_para_entity_com_defaults_defensivos() -> None:
    did, tid = uuid4(), uuid4()
    row = _row_minima(did, tid)
    row["score_completo"] = {"bad": "shape"}
    row_valid_sc = _row_minima(uuid4(), uuid4())
    row_valid_sc["score_completo"] = {
        "score_geral": {"valor": 70.0, "peso_total_aplicado": 1.0},
        "score_por_dimensao": {
            "fiscal": {"valor": 70.0, "peso_total_aplicado": 1.0},
        },
    }
    row_valid_sc["empresa_faixa_faturamento"] = "ate_360_mil"
    ent_sc = _row_dict_para_entity(row_valid_sc)
    assert ent_sc.score_completo_snapshot is not None
    assert ent_sc.empresa.faixa_faturamento == FaixaFaturamentoDeclarada.ATE_360_MIL

    row["respondente_email"] = None
    row["empresa_faixa_faturamento"] = "invalida"
    row["empresa_cnae"] = "   "
    row["checklist_m12_estado"] = ["x"] * 10
    row["aceite_termos_privacidade_em"] = "2026-05-09T10:00:00Z"
    row["quadro_implantacao_anotacoes"] = {"k": {"comentario": "ok"}}
    row["explicacao_score_llm"] = {
        "text": "persistida",
        "provider": "p",
        "model": "m",
        "policy_version": "v",
    }
    entity = _row_dict_para_entity(row)
    assert entity.explicacao_score_llm is not None
    assert entity.explicacao_score_llm["text"] == "persistida"
    assert entity.respondente.email == "nao-informado@placeholder.qdi"
    assert entity.empresa.faixa_faturamento is None
    assert entity.empresa.cnae_principal == "6201500"
    assert entity.checklist_m12_estado is None
    assert entity.aceite_termos_privacidade_em is not None


def test_patch_explicacao_score_llm_sync_sucesso_e_nao_encontrado() -> None:
    did, tid = uuid4(), uuid4()
    snap = {"text": "ok", "provider": "p", "model": "m", "policy_version": "v"}
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn = _mock_conn_cursor(mock_cursor)
    with patch(
        "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
        return_value=mock_conn,
    ):
        _patch_explicacao_score_llm_sync("postgresql://u:p@localhost:1/db", did, tid, snap)
    mock_conn.commit.assert_called_once()

    mock_cursor2 = MagicMock()
    mock_cursor2.rowcount = 0
    mock_conn2 = _mock_conn_cursor(mock_cursor2)
    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn2,
        ),
        pytest.raises(ValueError, match="não encontrado"),
    ):
        _patch_explicacao_score_llm_sync("postgresql://u:p@localhost:1/db", did, tid, snap)


@pytest.mark.parametrize(
    "fn,args",
    [
        (_patch_relatorio_sync, ("http://x.pdf", 1)),
        (_patch_quadro_sync, ({"f0_a0": {"comentarios": [], "prazo_meta": ""}}, 1)),
        (_patch_m12_sync, ([1] * 10, 1)),
        (_patch_explicacao_score_llm_sync, ({"text": "x"},)),
    ],
)
def test_patch_sync_rollback_em_excecao(fn, args) -> None:
    did, tid = uuid4(), uuid4()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("erro update")
    mock_conn = _mock_conn_cursor(mock_cursor)
    with (
        patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ),
        pytest.raises(RuntimeError, match="erro update"),
    ):
        fn("postgresql://u:p@localhost:1/db", did, tid, *args)
    mock_conn.rollback.assert_called_once()
