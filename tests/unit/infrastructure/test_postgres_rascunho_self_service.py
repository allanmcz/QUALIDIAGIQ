"""Testes do store síncrono de rascunhos self-service (mock de psycopg2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.infrastructure.repositories.postgres_rascunho_self_service import (
    buscar_rascunho_ativo_por_token_sync,
    inserir_rascunho_sync,
    marcar_rascunho_consumido_sync,
)


class _FakeCursor:
    def __init__(self, factory: Any) -> None:
        self._factory = factory

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, *args: object, **kwargs: object) -> None:
        self._factory.on_execute(*args, **kwargs)

    def fetchone(self) -> Any:
        return self._factory.on_fetchone()


class _FakeConn:
    def __init__(self, factory: Any) -> None:
        self._factory = factory

    def __enter__(self) -> _FakeConn:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def cursor(
        self, *args: object, cursor_factory: object | None = None, **kwargs: object
    ) -> _FakeCursor:
        del cursor_factory, args, kwargs
        return _FakeCursor(self._factory)

    def commit(self) -> None:
        self._factory.committed = True

    def rollback(self) -> None:
        self._factory.rolled_back = True

    def close(self) -> None:
        pass


class _ConnFactory:
    def __init__(
        self,
        fetch_rows: list[Any],
        *,
        execute_error: Exception | None = None,
    ) -> None:
        self.fetch_rows = list(fetch_rows)
        self.execute_error = execute_error
        self.executes: list[tuple[Any, ...]] = []
        self.committed = False
        self.rolled_back = False

    def connect(self, _dsn: str) -> _FakeConn:
        return _FakeConn(self)

    def on_execute(self, *args: object, **kwargs: object) -> None:
        if self.execute_error is not None:
            raise self.execute_error
        self.executes.append((args, kwargs))

    def on_fetchone(self) -> Any:
        if not self.fetch_rows:
            return None
        return self.fetch_rows.pop(0)


@pytest.fixture
def patch_psycopg2_connect(monkeypatch: pytest.MonkeyPatch) -> Any:
    def _patch(factory: _ConnFactory) -> None:
        monkeypatch.setattr(
            "src.infrastructure.repositories.postgres_rascunho_self_service.psycopg2.connect",
            factory.connect,
        )

    return _patch


def test_inserir_rascunho_insere_e_devolve_token(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    rid = uuid4()
    f = _ConnFactory(fetch_rows=[(str(rid),)])
    patch_psycopg2_connect(f)
    tid = uuid4()
    token, exp, rid_out = inserir_rascunho_sync(
        "postgresql://test",
        tenant_id=tid,
        email_norm="lead@example.com",
        payload_dict={"k": 1},
    )
    assert f.committed is True
    assert len(token) > 20
    assert exp.tzinfo is not None
    assert rid_out == rid


def test_buscar_ativo_none_quando_sem_linha(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    f = _ConnFactory(fetch_rows=[None])
    patch_psycopg2_connect(f)
    assert buscar_rascunho_ativo_por_token_sync("postgresql://test", "qualquer-token") is None


def test_buscar_ativo_none_quando_consumido(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "a@b.com",
        "payload_json": {},
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": datetime.now(UTC),
    }
    f = _ConnFactory(fetch_rows=[row])
    patch_psycopg2_connect(f)
    assert buscar_rascunho_ativo_por_token_sync("postgresql://test", "tok") is None


def test_buscar_ativo_retorna_dict_quando_valido(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "a@b.com",
        "payload_json": {"empresa": {"razao_social": "X"}},
        "expira_em": datetime.now(UTC) + timedelta(days=1),
        "consumido_em": None,
    }
    f = _ConnFactory(fetch_rows=[row])
    patch_psycopg2_connect(f)
    out = buscar_rascunho_ativo_por_token_sync("postgresql://test", "x" * 20)
    assert out is not None
    assert out["email_norm"] == "a@b.com"


def test_buscar_ativo_none_quando_expira_em_nulo(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "a@b.com",
        "payload_json": {},
        "expira_em": None,
        "consumido_em": None,
    }
    f = _ConnFactory(fetch_rows=[row])
    patch_psycopg2_connect(f)
    assert buscar_rascunho_ativo_por_token_sync("postgresql://test", "z" * 20) is None


def test_buscar_ativo_none_quando_expirado(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "a@b.com",
        "payload_json": {},
        "expira_em": datetime.now(UTC) - timedelta(minutes=1),
        "consumido_em": None,
    }
    f = _ConnFactory(fetch_rows=[row])
    patch_psycopg2_connect(f)
    assert buscar_rascunho_ativo_por_token_sync("postgresql://test", "x" * 20) is None


def test_buscar_ativo_parse_expira_string_sem_tz(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "a@b.com",
        "payload_json": {"empresa": {"razao_social": "Y"}},
        "expira_em": (datetime.now(UTC) + timedelta(days=1)).replace(tzinfo=None),
        "consumido_em": None,
    }
    f = _ConnFactory(fetch_rows=[row])
    patch_psycopg2_connect(f)
    out = buscar_rascunho_ativo_por_token_sync("postgresql://test", "y" * 20)
    assert out is not None


def test_marcar_consumido_executa_update(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    f = _ConnFactory(fetch_rows=[])
    patch_psycopg2_connect(f)
    marcar_rascunho_consumido_sync("postgresql://test", UUID(str(uuid4())))
    assert f.committed is True


def test_inserir_rascunho_rollback_quando_execute_falha(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    f = _ConnFactory(fetch_rows=[], execute_error=RuntimeError("disc cheio"))
    patch_psycopg2_connect(f)
    with pytest.raises(RuntimeError, match="disc cheio"):
        inserir_rascunho_sync(
            "postgresql://test",
            tenant_id=uuid4(),
            email_norm="e@x.com",
            payload_dict={},
        )
    assert f.rolled_back is True
    assert f.committed is False


def test_inserir_rascunho_erro_quando_returning_id_ausente(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    """Defesa: INSERT sem id devolvido não deve commitar estado inconsistente."""
    f = _ConnFactory(fetch_rows=[(None,)])
    patch_psycopg2_connect(f)
    with pytest.raises(RuntimeError, match="RETURNING id"):
        inserir_rascunho_sync(
            "postgresql://test",
            tenant_id=uuid4(),
            email_norm="e@x.com",
            payload_dict={},
        )
    assert f.rolled_back is True
    assert f.committed is False


def test_marcar_consumido_rollback_quando_execute_falha(
    monkeypatch: pytest.MonkeyPatch, patch_psycopg2_connect: Any
) -> None:
    f = _ConnFactory(fetch_rows=[], execute_error=OSError("io"))
    patch_psycopg2_connect(f)
    with pytest.raises(OSError, match="io"):
        marcar_rascunho_consumido_sync("postgresql://test", UUID(str(uuid4())))
    assert f.rolled_back is True
