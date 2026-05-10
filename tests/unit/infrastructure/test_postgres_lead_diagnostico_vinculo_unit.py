"""Testes unitários de vinculação lead→tenant via Postgres (sem container)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo import (
    PostgresLeadDiagnosticoVinculoAdapter,
    vincular_gratuitos_self_service_sync,
)


def test_vincular_sync_retorna_uuids_e_commit() -> None:
    uid = uuid4()
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = [{"id": str(uid)}, {"id": None}]
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None

    ts, td = uuid4(), uuid4()
    with patch(
        "src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo.psycopg2.connect",
        return_value=conn,
    ):
        out = vincular_gratuitos_self_service_sync(
            "postgresql://u:p@host/db",
            tenant_self_service=ts,
            tenant_destino=td,
            email_admin_normalizado="  Admin@Test.COM ",
        )

    assert out == [uid]
    conn.commit.assert_called_once()
    conn.close.assert_called_once()
    chamadas_sql = cur.execute.call_args[0][1]
    assert chamadas_sql["email"] == "admin@test.com"


def test_vincular_sync_rollback_quando_execute_falha() -> None:
    conn = MagicMock()
    cur = MagicMock()
    cur.execute.side_effect = RuntimeError("sql")
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None

    with (
        patch(
            "src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo.psycopg2.connect",
            return_value=conn,
        ),
        pytest.raises(RuntimeError, match="sql"),
    ):
        vincular_gratuitos_self_service_sync(
            "postgresql://x",
            tenant_self_service=uuid4(),
            tenant_destino=uuid4(),
            email_admin_normalizado="a@b.com",
        )

    conn.rollback.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_adapter_vincular_delega_sync_via_to_thread() -> None:
    esperado = uuid4()
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = [{"id": str(esperado)}]
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None

    async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
        return fn(*args, **kwargs)

    adapter = PostgresLeadDiagnosticoVinculoAdapter("postgresql://sync/db")
    with (
        patch(
            "src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo.psycopg2.connect",
            return_value=conn,
        ),
        patch(
            "src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo.asyncio.to_thread",
            side_effect=run_imediato,
        ),
    ):
        out = await adapter.vincular_gratuitos_self_service_para_tenant(
            email_admin_normalizado="z@z.com",
            tenant_destino=uuid4(),
            tenant_self_service=uuid4(),
        )

    assert out == [esperado]
