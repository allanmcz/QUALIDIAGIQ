"""
Integração PostgreSQL — função ``qdi_cleanup_idempotency()`` (migração 0032).

Requer Postgres com migrações aplicadas e coluna ``tenant_id`` em ``idempotency_responses`` (0019).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import asyncpg
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)

_ZERO_TENANT = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def pg_conn():
    try:
        conn = await asyncpg.connect(POSTGRES_URL, timeout=5)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev` ou defina QDI_POSTGRES_TEST_URL")
    try:
        yield conn
    finally:
        await conn.close()


async def _garantir_funcao_cleanup(pg_conn: asyncpg.Connection) -> None:
    existe = await pg_conn.fetchval("""
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'qdi_cleanup_idempotency'
        """)
    if existe is None:
        sql = (
            _REPO_ROOT / "src/infrastructure/db/migrations/0032_pgcron_cleanup_idempotency.sql"
        ).read_text(encoding="utf-8")
        await pg_conn.execute(sql)


async def _garantir_force_rls(pg_conn: asyncpg.Connection) -> None:
    force = await pg_conn.fetchval("""
        SELECT c.relforcerowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'diagnosticos'
        """)
    if force is not True:
        sql = (
            _REPO_ROOT / "src/infrastructure/db/migrations/0033_force_rls_tabelas_criticas.sql"
        ).read_text(encoding="utf-8")
        await pg_conn.execute(sql)


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_qdi_cleanup_idempotency_remove_apenas_expirados(pg_conn: asyncpg.Connection) -> None:
    """Remove só linhas com ``expira_em`` no passado; preserva vigentes."""
    await _garantir_funcao_cleanup(pg_conn)

    exp_keys = [hashlib.sha256(f"exp-{i}".encode()).hexdigest() for i in range(100)]
    val_keys = [hashlib.sha256(f"val-{i}".encode()).hexdigest() for i in range(50)]
    todos = exp_keys + val_keys

    for h in exp_keys:
        await pg_conn.execute(
            """
            INSERT INTO idempotency_responses (
                chave_hash, status_code, body, headers_json, expira_em, tenant_id
            )
            VALUES ($1, 200, $2::bytea, '{}'::jsonb, now() - interval '1 day', $3::uuid)
            ON CONFLICT (chave_hash) DO UPDATE SET expira_em = EXCLUDED.expira_em
            """,
            h,
            b"{}",
            _ZERO_TENANT,
        )
    for h in val_keys:
        await pg_conn.execute(
            """
            INSERT INTO idempotency_responses (
                chave_hash, status_code, body, headers_json, expira_em, tenant_id
            )
            VALUES ($1, 200, $2::bytea, '{}'::jsonb, now() + interval '1 day', $3::uuid)
            ON CONFLICT (chave_hash) DO UPDATE SET expira_em = EXCLUDED.expira_em
            """,
            h,
            b"{}",
            _ZERO_TENANT,
        )

    row = await pg_conn.fetchrow("SELECT * FROM qdi_cleanup_idempotency()")
    assert row is not None
    assert int(row[0]) >= 100

    restantes = await pg_conn.fetchval(
        "SELECT count(*) FROM idempotency_responses WHERE chave_hash = ANY($1::text[])",
        todos,
    )
    assert restantes == 50

    await pg_conn.execute(
        "DELETE FROM idempotency_responses WHERE chave_hash = ANY($1::text[])",
        todos,
    )


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_diagnosticos_force_rls_flag(pg_conn: asyncpg.Connection) -> None:
    """Tabela ``diagnosticos`` deve ter ``relforcerowsecurity`` após migração 0033."""
    await _garantir_force_rls(pg_conn)

    force = await pg_conn.fetchval("""
        SELECT c.relforcerowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'diagnosticos'
        """)
    assert force is True
