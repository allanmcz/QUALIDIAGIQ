"""
Verifica artefatos da migração 0019 (RLS admins + idempotency tenant-scoped).

Requer Postgres com migrações aplicadas — marcador ``postgres``.
"""

from __future__ import annotations

import os

import pytest

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)


@pytest.fixture
async def pg_conn():
    import asyncpg

    try:
        conn = await asyncpg.connect(POSTGRES_URL, timeout=5)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev` ou defina QDI_POSTGRES_TEST_URL")
    try:
        yield conn
    finally:
        await conn.close()


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_idempotency_responses_tem_tenant_id_not_null(pg_conn):
    val = await pg_conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'idempotency_responses'
          AND column_name = 'tenant_id'
          AND is_nullable = 'NO'
    """)
    assert val == 1


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_admins_e_idempotency_com_rls(pg_conn):
    adm = await pg_conn.fetchval("""
        SELECT c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'admins'
    """)
    assert adm is True

    idem = await pg_conn.fetchval("""
        SELECT c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'idempotency_responses'
    """)
    assert idem is True

    n_pol_adm = await pg_conn.fetchval("""
        SELECT count(*)::int FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'admins'
    """)
    assert (n_pol_adm or 0) >= 1

    n_pol_idem = await pg_conn.fetchval("""
        SELECT count(*)::int FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'idempotency_responses'
    """)
    assert (n_pol_idem or 0) >= 1
