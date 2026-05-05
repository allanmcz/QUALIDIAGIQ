"""Testes de ``postgres_plano_painel_sync`` com mocks de psycopg2 (sem PostgreSQL real)."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.application.services.plano_painel_derivacao import (
    DerivacaoPlanoMaterializado,
    LinhaPlanoAcaoParaPersistir,
    LinhaPlanoCronogramaParaPersistir,
    LinhaPlanoMatrizParaPersistir,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.infrastructure.repositories import postgres_plano_painel_sync as m


def _diagnostico_min(tenant_id, did) -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Sync Test",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    return Diagnostico(
        tenant_id=tenant_id, id=did, empresa=emp, respondente=Respondente(email="t@t.com")
    )


def _deriv_min(acao_id, versao_plano: int = 1) -> DerivacaoPlanoMaterializado:
    ln = LinhaPlanoAcaoParaPersistir(
        id=acao_id,
        ordem_exibicao=1,
        frente_indice=0,
        acao_indice=0,
        frente_nome="Fiscal",
        texto_acao="Ação",
        responsavel_sugerido="Fiscal",
        prazo_sugerido_texto="30d",
        criticidade="alta",
        base_legal="LC 214/2025",
        origem_motor="OUTROS",
        prioridade_motor=1,
    )
    mat = LinhaPlanoMatrizParaPersistir(
        id=uuid4(),
        ordem_exibicao=1,
        departamento="Fiscal",
        impacto_resumo="Alto",
        criticidade="alta",
        base_legal=None,
    )
    cro = LinhaPlanoCronogramaParaPersistir(
        id=uuid4(),
        ordem_exibicao=1,
        fase="Fase 1",
        foco="Foco",
        referencia_normativa="EC 132/2023",
    )
    ser = PlanoPainelSerializado(
        versao_plano=versao_plano,
        checklist=(),
        matriz_impacto=(),
        cronograma=(),
    )
    return DerivacaoPlanoMaterializado(
        versao_plano=versao_plano,
        linhas_acao=(ln,),
        linhas_matriz=(mat,),
        linhas_cronograma=(cro,),
        serializado_http=ser,
    )


class TestSubtarefaRowParaHttp:
    """Conversão de linha SQL → dict HTTP (prazo date/datetime/str)."""

    def test_prazo_none(self) -> None:
        r = {"id": uuid4(), "titulo": "T", "status": "aberta", "ordem": 1, "comentarios": None}
        out = m._subtarefa_row_para_http(r)
        assert out["prazo"] is None

    def test_prazo_datetime(self) -> None:
        d = datetime(2026, 5, 1, 12, 0, 0)
        r = {"id": uuid4(), "titulo": "T", "status": "aberta", "ordem": 1, "prazo": d}
        out = m._subtarefa_row_para_http(r)
        assert out["prazo"] == "2026-05-01"

    def test_prazo_string_trunca(self) -> None:
        r = {
            "id": uuid4(),
            "titulo": "T",
            "status": "aberta",
            "ordem": 1,
            "prazo": "2026-05-04extra",
        }
        out = m._subtarefa_row_para_http(r)
        assert out["prazo"] == "2026-05-04"


def test_materializar_plano_em_conexao_executa_sql() -> None:
    tid, did, aid = uuid4(), uuid4(), uuid4()
    diag = _diagnostico_min(tid, did)
    deriv = _deriv_min(aid)
    mock_cur = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    m.materializar_plano_em_conexao(mock_conn, diag, deriv)
    assert mock_cur.execute.call_count >= 6


@patch.object(m.psycopg2, "connect")
def test_plano_materializado_existe(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (1,)
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    assert m.plano_materializado_existe_sync("postgresql://x", uuid4(), uuid4(), 1) is True
    mock_conn.close.assert_called_once()


@patch.object(m.psycopg2, "connect")
def test_plano_materializado_nao_existe(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    assert m.plano_materializado_existe_sync("postgresql://x", uuid4(), uuid4(), 1) is False


@patch.object(m.psycopg2, "connect")
def test_buscar_plano_serializado_sem_acoes(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    assert m.buscar_plano_painel_serializado_sync("postgresql://x", uuid4(), uuid4()) is None


@patch.object(m.psycopg2, "connect")
def test_buscar_plano_serializado_com_acao_e_sub(mock_connect: MagicMock) -> None:
    tid_u, did_u, aid_u = uuid4(), uuid4(), uuid4()
    aid = str(aid_u)
    acao = {
        "id": aid,
        "versao_plano": 1,
        "frente_indice": 0,
        "acao_indice": 0,
        "ordem_exibicao": 1,
        "frente_nome": "F1",
        "texto_acao": "Texto",
        "responsavel_sugerido": "Resp",
        "prazo_sugerido_texto": "30d",
        "criticidade": "media",
        "base_legal": "LC 214/2025",
        "prioridade_motor": 2,
    }
    mat = {
        "departamento": "Fiscal",
        "impacto_resumo": "I",
        "criticidade": "media",
        "base_legal": None,
    }
    cro = {"fase": "1", "foco": "X", "referencia_normativa": "EC 132/2023"}
    sub = {
        "id": str(uuid4()),
        "plano_acao_id": aid,
        "titulo": "Sub",
        "status": "aberta",
        "ordem": 1,
        "prazo": None,
        "comentarios": None,
    }
    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = [[acao], [mat], [cro], [sub]]
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.buscar_plano_painel_serializado_sync("postgresql://x", did_u, tid_u)
    assert out is not None
    assert out.versao_plano == 1
    assert len(out.checklist) == 1
    assert out.checklist[0]["acoes"][0]["plano_acao_id"] == aid


@patch.object(m.psycopg2, "connect")
def test_inserir_subtarefa_sync_acao_inexistente(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    with pytest.raises(ValueError, match="inexistente"):
        m.inserir_subtarefa_sync("postgresql://x", uuid4(), uuid4(), uuid4(), "x", 1)


@patch.object(m.psycopg2, "connect")
def test_inserir_subtarefa_sync_sucesso(mock_connect: MagicMock) -> None:
    tid, did, aid = uuid4(), uuid4(), uuid4()
    row = {
        "id": str(uuid4()),
        "titulo": "Nova",
        "status": "aberta",
        "ordem": 1,
        "prazo": None,
        "comentarios": None,
    }
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [(1,), row]
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.inserir_subtarefa_sync("postgresql://x", tid, did, aid, "Nova", 1)
    assert out["titulo"] == "Nova"
    mock_conn.commit.assert_called_once()


@patch.object(m.psycopg2, "connect")
def test_atualizar_subtarefa_sync_select_sem_linha(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.atualizar_subtarefa_sync(
        "postgresql://x",
        uuid4(),
        uuid4(),
        uuid4(),
        titulo=None,
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is None


@patch.object(m.psycopg2, "connect")
def test_atualizar_subtarefa_sync_sem_patch_retorna_select(mock_connect: MagicMock) -> None:
    tid, did, sid = uuid4(), uuid4(), uuid4()
    row = {
        "id": str(sid),
        "titulo": "Lida",
        "status": "feita",
        "ordem": 0,
        "prazo": None,
        "comentarios": "ok",
    }
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = row
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.atualizar_subtarefa_sync(
        "postgresql://x",
        tid,
        did,
        sid,
        titulo=None,
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is not None
    assert out["titulo"] == "Lida"


@patch.object(m.psycopg2, "connect")
def test_inserir_subtarefa_sync_rollback_em_erro(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [(1,), None]
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    with pytest.raises(AssertionError):
        m.inserir_subtarefa_sync("postgresql://x", uuid4(), uuid4(), uuid4(), "t", 1)
    mock_conn.rollback.assert_called_once()


@patch.object(m.psycopg2, "connect")
def test_atualizar_subtarefa_sync_varios_campos(mock_connect: MagicMock) -> None:
    tid, did, sid = uuid4(), uuid4(), uuid4()
    row = {
        "id": str(sid),
        "titulo": "T",
        "status": "feita",
        "ordem": 3,
        "prazo": date(2026, 1, 15),
        "comentarios": "nota",
    }
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = row
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.atualizar_subtarefa_sync(
        "postgresql://x",
        tid,
        did,
        sid,
        titulo=None,
        status="  feita  ",
        prazo=date(2026, 1, 15),
        comentarios="nota",
        ordem=3,
    )
    assert out is not None
    assert out["ordem"] == 3


@patch.object(m.psycopg2, "connect")
def test_atualizar_subtarefa_sync_update_execute_falha(mock_connect: MagicMock) -> None:
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = RuntimeError("db down")
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    with pytest.raises(RuntimeError, match="db down"):
        m.atualizar_subtarefa_sync(
            "postgresql://x",
            uuid4(),
            uuid4(),
            uuid4(),
            titulo="x",
            status=None,
            prazo=None,
            comentarios=None,
            ordem=None,
        )
    mock_conn.rollback.assert_called_once()


@patch.object(m.psycopg2, "connect")
def test_atualizar_subtarefa_sync_com_titulo(mock_connect: MagicMock) -> None:
    tid, did, sid = uuid4(), uuid4(), uuid4()
    row = {
        "id": str(sid),
        "titulo": "Atual",
        "status": "aberta",
        "ordem": 2,
        "prazo": date(2026, 6, 1),
        "comentarios": None,
    }
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = row
    cm = MagicMock()
    cm.__enter__.return_value = mock_cur
    cm.__exit__.return_value = False
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cm
    mock_connect.return_value = mock_conn
    out = m.atualizar_subtarefa_sync(
        "postgresql://x",
        tid,
        did,
        sid,
        titulo="  Atual  ",
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is not None
    assert out["titulo"] == "Atual"
    mock_conn.commit.assert_called_once()
