"""Testes do backend Postgres de idempotência (SQLAlchemy sync)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia
from src.infrastructure.idempotency.postgres_backend import (
    idempotency_cleanup_expired,
    idempotency_get,
    idempotency_put,
)

_TID = UUID("00000000-0000-0000-0000-000000000000")


@pytest.fixture
def mock_engine() -> MagicMock:
    eng = MagicMock()
    conn = MagicMock()
    row_hit = {
        "status_code": 201,
        "body": b'{"ok":true}',
        "headers_json": {"content-type": "application/json"},
    }

    def exec_side_effect(stmt: object, params: dict | None = None):
        sql = str(stmt)
        if "SELECT status_code" in sql:
            mr = MagicMock()
            if params and params.get("h") == "hit":
                mr.mappings.return_value.first.return_value = row_hit
            else:
                mr.mappings.return_value.first.return_value = None
            return mr
        return MagicMock()

    conn.execute.side_effect = exec_side_effect

    connect_cm = MagicMock()
    connect_cm.__enter__.return_value = conn
    connect_cm.__exit__.return_value = None
    eng.connect.return_value = connect_cm

    begin_cm = MagicMock()
    begin_cm.__enter__.return_value = conn
    begin_cm.__exit__.return_value = None
    eng.begin.return_value = begin_cm

    return eng


def test_idempotency_get_miss(mock_engine: MagicMock) -> None:
    assert idempotency_get(mock_engine, "miss", _TID) is None


def test_idempotency_get_hit(mock_engine: MagicMock) -> None:
    hit = idempotency_get(mock_engine, "hit", _TID)
    assert hit is not None
    assert hit.status_code == 201
    assert hit.body == b'{"ok":true}'
    assert ("content-type", "application/json") in hit.headers


def test_idempotency_cleanup_expired_executa_delete(mock_engine: MagicMock) -> None:
    conn = mock_engine.begin.return_value.__enter__.return_value
    conn.execute.reset_mock()

    idempotency_cleanup_expired(mock_engine)

    chamadas_sql = [str(c.args[0]) for c in conn.execute.call_args_list if c.args]
    assert any("DELETE FROM idempotency_responses" in s for s in chamadas_sql)


def test_idempotency_put_executa_insert(mock_engine: MagicMock) -> None:
    cached = CorpoCacheadoIdempotencia(
        status_code=200,
        body=b"x",
        headers=(("Content-Type", "application/json"),),
    )
    conn = mock_engine.connect.return_value.__enter__.return_value
    idempotency_put(mock_engine, "abc123", cached, 60, _TID)
    assert conn.execute.call_count >= 2
