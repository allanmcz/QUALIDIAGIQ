"""Testes — ``PostgresCnpjConsultaRepository`` com ``psycopg2`` mockado."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro
from src.infrastructure.repositories.postgres_cnpj_consulta_repository import (
    PostgresCnpjConsultaRepository,
)


def _fake_conn_cur(fetchone_return: dict[str, object] | None) -> tuple[MagicMock, MagicMock]:
    conn = MagicMock()
    cur = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = None
    conn.cursor.return_value = cm
    cur.fetchone.return_value = fetchone_return
    return conn, cur


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_buscar_por_idempotencia_none(mock_connect: MagicMock) -> None:
    conn, _ = _fake_conn_cur(None)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    assert repo.buscar_por_idempotencia(uuid4(), "nao-existe") is None


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_buscar_cache_valido_none(mock_connect: MagicMock) -> None:
    conn, _ = _fake_conn_cur(None)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    assert repo.buscar_ultimo_cache_valido_triplo_ttl(uuid4(), "33014556000196") is None


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_buscar_por_idempotencia(mock_connect: MagicMock) -> None:
    tid = uuid4()
    rid = uuid4()
    row = {
        "id": rid,
        "cnpj": "33014556000196",
        "payload_bruto": {},
        "payload_canonico": {"cnpj": "33014556000196"},
        "fonte": "brasil_api",
        "expira_cadastral_at": datetime.now(UTC),
        "expira_qualificacao_at": datetime.now(UTC),
        "expira_situacao_at": datetime.now(UTC),
    }
    conn, _ = _fake_conn_cur(row)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    out = repo.buscar_por_idempotencia(tid, "abc")
    assert out is not None
    assert out["id"] == rid
    conn.close.assert_called_once()


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_inserir_consulta_sem_returning_falha(mock_connect: MagicMock) -> None:
    conn, cur = _fake_conn_cur(None)
    cur.fetchone.return_value = None
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    consultado = datetime.now(UTC)
    with pytest.raises(RuntimeError, match="INSERT"):
        repo.inserir_consulta(
            tenant_id=uuid4(),
            idempotency_key="k",
            cnpj="33014556000196",
            diagnostico_id=None,
            payload_bruto={},
            payload_canonico={"cnpj": "33014556000196"},
            payload_hash="a" * 64,
            fonte="brasil_api",
            consultado_em=consultado,
            expira_cadastral_at=consultado,
            expira_qualificacao_at=consultado,
            expira_situacao_at=consultado,
            latencia_ms=10,
            http_status=200,
            trace_id=None,
        )


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_inserir_consulta_retorna_uuid(mock_connect: MagicMock) -> None:
    novo = uuid4()
    conn, cur = _fake_conn_cur(None)
    cur.fetchone.return_value = (str(novo),)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    consultado = datetime.now(UTC)
    uid = repo.inserir_consulta(
        tenant_id=uuid4(),
        idempotency_key="k",
        cnpj="33014556000196",
        diagnostico_id=None,
        payload_bruto={},
        payload_canonico={"cnpj": "33014556000196"},
        payload_hash="a" * 64,
        fonte="brasil_api",
        consultado_em=consultado,
        expira_cadastral_at=consultado,
        expira_qualificacao_at=consultado,
        expira_situacao_at=consultado,
        latencia_ms=10,
        http_status=200,
        trace_id=None,
    )
    assert uid == novo
    conn.commit.assert_called_once()


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_atualizar_rejeita_diagnostico_inexistente(mock_connect: MagicMock) -> None:
    conn, _ = _fake_conn_cur(None)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    emp = EmpresaInfo(
        cnpj="33014556000196",
        razao_social="NOVA",
        porte=PorteEmpresa.MEDIO,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="4711302",
        uf="RJ",
        setor_macro=SetorMacro.COMERCIO,
    )
    with pytest.raises(ValueError, match="não encontrado"):
        repo.atualizar_empresa_diagnostico_em_andamento(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            nova_empresa=emp,
            historico=[("empresa_razao_social", "OLD", "NOVA")],
            cnpj_consulta_id=None,
        )


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_atualizar_rejeita_finalizado(mock_connect: MagicMock) -> None:
    conn, _ = _fake_conn_cur({"status": "finalizado"})
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    emp = EmpresaInfo(
        cnpj="33014556000196",
        razao_social="NOVA",
        porte=PorteEmpresa.MEDIO,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="4711302",
        uf="RJ",
        setor_macro=SetorMacro.COMERCIO,
    )
    with pytest.raises(ValueError, match="em_andamento"):
        repo.atualizar_empresa_diagnostico_em_andamento(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            nova_empresa=emp,
            historico=[("empresa_razao_social", "OLD", "NOVA")],
            cnpj_consulta_id=None,
        )


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_atualizar_em_andamento_executa_update(mock_connect: MagicMock) -> None:
    tid, did = uuid4(), uuid4()
    conn, cur = _fake_conn_cur({"status": "em_andamento"})
    cur.rowcount = 1
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    emp = EmpresaInfo(
        cnpj="33014556000196",
        razao_social="NOVA",
        porte=PorteEmpresa.MEDIO,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="4711302",
        uf="RJ",
        setor_macro=SetorMacro.COMERCIO,
    )
    repo.atualizar_empresa_diagnostico_em_andamento(
        tenant_id=tid,
        diagnostico_id=did,
        nova_empresa=emp,
        historico=[("empresa_razao_social", "OLD", "NOVA")],
        cnpj_consulta_id=uuid4(),
    )
    assert cur.execute.call_count >= 3
    conn.commit.assert_called_once()


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_inserir_consulta_normaliza_naive_datetime(mock_connect: MagicMock) -> None:
    """Branch ``consultado_em.tzinfo is None`` alinha UTC antes do INSERT."""
    novo = uuid4()
    conn, cur = _fake_conn_cur(None)
    cur.fetchone.return_value = (str(novo),)
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    naive = datetime(2030, 1, 2, 12, 0, 0)
    uid_ins = repo.inserir_consulta(
        tenant_id=uuid4(),
        idempotency_key="k",
        cnpj="33014556000196",
        diagnostico_id=None,
        payload_bruto={},
        payload_canonico={"cnpj": "33014556000196"},
        payload_hash="b" * 64,
        fonte="minha_receita",
        consultado_em=naive,
        expira_cadastral_at=naive,
        expira_qualificacao_at=naive,
        expira_situacao_at=naive,
        latencia_ms=None,
        http_status=200,
        trace_id=None,
    )
    assert uid_ins == novo


@patch("src.infrastructure.repositories.postgres_cnpj_consulta_repository.psycopg2.connect")
def test_atualizar_rowcount_update_zero_falha(mock_connect: MagicMock) -> None:
    conn, cur = _fake_conn_cur({"status": "em_andamento"})
    cur.rowcount = 0
    mock_connect.return_value = conn
    repo = PostgresCnpjConsultaRepository("postgresql://mock")
    emp = EmpresaInfo(
        cnpj="33014556000196",
        razao_social="NOVA",
        porte=PorteEmpresa.MEDIO,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="4711302",
        uf="RJ",
        setor_macro=SetorMacro.COMERCIO,
    )
    with pytest.raises(ValueError, match="Não foi possível atualizar empresa"):
        repo.atualizar_empresa_diagnostico_em_andamento(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            nova_empresa=emp,
            historico=[],
            cnpj_consulta_id=uuid4(),
        )
