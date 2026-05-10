"""Testes do router de manutenção admin (Presentation)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.presentation.api.dependencies import get_current_user_tenant
from src.presentation.api.main import app
from src.presentation.api.routers import admin_maintenance_router as amr

client = TestClient(app)


@pytest.fixture(autouse=True)
def limpa_rate_limit_por_teste() -> None:
    """Evita 429 entre testes que partilham o mesmo dicionário global."""
    amr._LAST_CLEANUP_TS_BY_TENANT.clear()
    yield
    amr._LAST_CLEANUP_TS_BY_TENANT.clear()


def _usuario_gratuito() -> tuple[uuid.UUID, uuid.UUID, str]:
    return uuid.uuid4(), uuid.uuid4(), "gratuito"


@patch.object(amr, "get_settings")
@patch.object(amr.psycopg2, "connect", side_effect=OSError("indisponível"))
@pytest.mark.asyncio
async def test_connect_falha_dispara_finally_sem_conn(
    _mock_connect: MagicMock, mock_settings: MagicMock
) -> None:
    """Garante ramo ``conn is None`` no ``finally`` (cobertura de branch)."""
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"

    with pytest.raises(HTTPException) as ei:
        await amr.cleanup_idempotency(current=(uuid.uuid4(), uuid.uuid4(), "avancado"))
    assert ei.value.status_code == 500


def test_cleanup_idempotency_403_quando_gratuito() -> None:
    """Perfil gratuito não pode executar limpeza."""
    app.dependency_overrides[get_current_user_tenant] = _usuario_gratuito
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 403


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_200_avancado(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    """Fluxo feliz com perfil avançado e Postgres mockado."""
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
    mock_cur.fetchone.return_value = (7, ts)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_psycopg.connect.return_value = mock_conn

    uid = uuid.uuid4()
    tid = uuid.uuid4()

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uid, tid, "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    body = r.json()
    assert body["deleted_count"] == 7
    assert "2026-05-10" in body["executed_at"]
    mock_psycopg.connect.assert_called_once()


@patch.object(amr, "get_settings")
def test_cleanup_idempotency_503_sem_database(mock_settings: MagicMock) -> None:
    mock_settings.return_value.sync_database_url = None

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), uuid.uuid4(), "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 503


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_500_connect_falha(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"
    mock_psycopg.connect.side_effect = OSError("sem rede")

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), uuid.uuid4(), "admin"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 500


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_429_rate_limit(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (0, datetime.now(tz=UTC))
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_psycopg.connect.return_value = mock_conn

    tid = uuid.uuid4()

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), tid, "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r1 = client.post("/admin/maintenance/cleanup-idempotency")
        r2 = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r1.status_code == 200
    assert r2.status_code == 429


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_500_sem_linha_sql(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    """fetchone None deve produzir 500."""
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_psycopg.connect.return_value = mock_conn

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), uuid.uuid4(), "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 500


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_executed_at_sem_isoformat(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    """Instante sem método isoformat cai em str(ts)."""
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (1, "instante-legado")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_psycopg.connect.return_value = mock_conn

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), uuid.uuid4(), "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["executed_at"] == "instante-legado"


@patch.object(amr, "psycopg2")
@patch.object(amr, "get_settings")
def test_cleanup_idempotency_500_exec_sql(
    mock_settings: MagicMock, mock_psycopg: MagicMock
) -> None:
    mock_settings.return_value.sync_database_url = "postgresql://u:p@127.0.0.1:5432/db"
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = RuntimeError("sql")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.__exit__.return_value = None
    mock_psycopg.connect.return_value = mock_conn

    def _adv() -> tuple[uuid.UUID, uuid.UUID, str]:
        return uuid.uuid4(), uuid.uuid4(), "avancado"

    app.dependency_overrides[get_current_user_tenant] = _adv
    try:
        r = client.post("/admin/maintenance/cleanup-idempotency")
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 500
