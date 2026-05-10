"""Testes do adapter Postgres de retificações."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter import (
    PostgresDiagnosticoRetificacaoAdapter,
    _inserir_sync,
    _listar_sync,
    _row_para_model,
)


class TestRowParaModel:
    """Conversão de linha SQL → registo de domínio."""

    def test_payload_nao_dict_vira_dict_vazio(self) -> None:
        rid = uuid.uuid4()
        tid = uuid.uuid4()
        did = uuid.uuid4()
        row = {
            "id": str(rid),
            "tenant_id": str(tid),
            "diagnostico_original_id": str(did),
            "hash_diagnostico_original_sha256": "aa" * 32,
            "motivo_retificacao": "motivo longo suficiente",
            "payload_retificacao": [1, 2],
            "hash_retificacao_sha256": "bb" * 32,
            "actor_user_id": None,
            "criado_em": datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
        }
        r = _row_para_model(row)
        assert r.payload_retificacao == {}

    def test_actor_uuid_parseado(self) -> None:
        aid = uuid.uuid4()
        row = {
            "id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "diagnostico_original_id": str(uuid.uuid4()),
            "hash_diagnostico_original_sha256": "cc" * 32,
            "motivo_retificacao": "motivo longo suficiente",
            "payload_retificacao": {"x": 1},
            "hash_retificacao_sha256": "dd" * 32,
            "actor_user_id": str(aid),
            "criado_em": "2026-05-09T12:00:00Z",
        }
        r = _row_para_model(row)
        assert r.actor_user_id == aid


def _conn_com_cursor(fake_row: dict | None, rows_list: list | None = None):
    conn = MagicMock()
    cur_cm = MagicMock()
    cur = MagicMock()
    cur_cm.__enter__.return_value = cur
    cur_cm.__exit__.return_value = None
    conn.cursor.return_value = cur_cm
    if rows_list is not None:
        cur.fetchall.return_value = rows_list
    elif fake_row is not None:
        cur.fetchone.return_value = fake_row
    else:
        cur.fetchone.return_value = None
    return conn


@patch("src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.psycopg2.connect")
def test_inserir_sync_commit_e_retorna(mock_connect: MagicMock) -> None:
    rid = uuid.uuid4()
    tid = uuid.uuid4()
    did = uuid.uuid4()
    fake_row = {
        "id": str(rid),
        "tenant_id": str(tid),
        "diagnostico_original_id": str(did),
        "hash_diagnostico_original_sha256": "aa" * 32,
        "motivo_retificacao": "motivo longo suficiente",
        "payload_retificacao": {},
        "hash_retificacao_sha256": "bb" * 32,
        "actor_user_id": None,
        "criado_em": datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
    }
    mock_connect.return_value = _conn_com_cursor(fake_row)

    out = _inserir_sync(
        "postgresql://test",
        retificacao_id=rid,
        tenant_id=tid,
        diagnostico_original_id=did,
        hash_diagnostico_original_sha256="AA" * 32,
        motivo_retificacao="motivo longo suficiente",
        payload_retificacao={},
        hash_retificacao_sha256="BB" * 32,
        actor_user_id=None,
    )
    assert out.id == rid
    mock_connect.return_value.commit.assert_called_once()


@patch("src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.psycopg2.connect")
def test_inserir_sync_rollback_em_erro(mock_connect: MagicMock) -> None:
    conn = MagicMock()
    cur_cm = MagicMock()
    cur = MagicMock()
    cur_cm.__enter__.return_value = cur
    cur_cm.__exit__.return_value = None
    conn.cursor.return_value = cur_cm
    cur.execute.side_effect = RuntimeError("db")
    mock_connect.return_value = conn

    with pytest.raises(RuntimeError, match="db"):
        _inserir_sync(
            "postgresql://test",
            retificacao_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            diagnostico_original_id=uuid.uuid4(),
            hash_diagnostico_original_sha256="aa" * 32,
            motivo_retificacao="motivo longo suficiente",
            payload_retificacao={},
            hash_retificacao_sha256="bb" * 32,
            actor_user_id=None,
        )
    conn.rollback.assert_called_once()


@patch("src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.psycopg2.connect")
def test_inserir_sync_sem_linha_returning_erro(mock_connect: MagicMock) -> None:
    fake_row = None
    mock_connect.return_value = _conn_com_cursor(fake_row)

    with pytest.raises(RuntimeError, match="RETURNING"):
        _inserir_sync(
            "postgresql://test",
            retificacao_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            diagnostico_original_id=uuid.uuid4(),
            hash_diagnostico_original_sha256="aa" * 32,
            motivo_retificacao="motivo longo suficiente",
            payload_retificacao={},
            hash_retificacao_sha256="bb" * 32,
            actor_user_id=None,
        )


@patch("src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.psycopg2.connect")
def test_listar_sync_retorna_lista(mock_connect: MagicMock) -> None:
    tid = uuid.uuid4()
    did = uuid.uuid4()
    rid = uuid.uuid4()
    fake_row = {
        "id": str(rid),
        "tenant_id": str(tid),
        "diagnostico_original_id": str(did),
        "hash_diagnostico_original_sha256": "aa" * 32,
        "motivo_retificacao": "motivo longo suficiente",
        "payload_retificacao": {},
        "hash_retificacao_sha256": "bb" * 32,
        "actor_user_id": None,
        "criado_em": datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
    }
    mock_connect.return_value = _conn_com_cursor(None, rows_list=[fake_row])

    rows = _listar_sync(
        "postgresql://test",
        tenant_id=tid,
        diagnostico_original_id=did,
        limit=10,
    )
    assert len(rows) == 1
    assert rows[0].id == rid


@pytest.mark.asyncio
async def test_adapter_inserir_encaminha_para_sync() -> None:
    adapter = PostgresDiagnosticoRetificacaoAdapter(dsn_sync="postgresql://x")

    async def _immediate(fn: object, *a: object, **k: object) -> object:
        assert callable(fn)
        return fn(*a, **k)

    with (
        patch(
            "src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.asyncio.to_thread",
            new=_immediate,
        ),
        patch(
            "src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter._inserir_sync",
            return_value=MagicMock(),
        ) as sync_fn,
    ):
        rid = uuid.uuid4()
        tid = uuid.uuid4()
        did = uuid.uuid4()
        actor = uuid.uuid4()
        await adapter.inserir(
            retificacao_id=rid,
            tenant_id=tid,
            diagnostico_original_id=did,
            hash_diagnostico_original_sha256="aa" * 32,
            motivo_retificacao="motivo longo suficiente",
            payload_retificacao={},
            hash_retificacao_sha256="bb" * 32,
            actor_user_id=actor,
        )
        sync_fn.assert_called_once()


@pytest.mark.asyncio
async def test_adapter_listar_encaminha_para_sync() -> None:
    adapter = PostgresDiagnosticoRetificacaoAdapter(dsn_sync="postgresql://x")

    async def _immediate(fn: object, *a: object, **k: object) -> object:
        assert callable(fn)
        return fn(*a, **k)

    with (
        patch(
            "src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter.asyncio.to_thread",
            new=_immediate,
        ),
        patch(
            "src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter._listar_sync",
            return_value=[],
        ) as sync_fn,
    ):
        tid = uuid.uuid4()
        did = uuid.uuid4()
        await adapter.listar_por_diagnostico(
            tenant_id=tid,
            diagnostico_original_id=did,
            limit=5,
        )
        sync_fn.assert_called_once()
