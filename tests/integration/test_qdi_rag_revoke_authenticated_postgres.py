"""
QDI-H-003 — Garantir que o role ``authenticated`` não tem privilégios de escrita em ``qdi_rag.documento_normativo``.

Requer Postgres com migrações até ``0037_revoke_qdi_rag_writes_authenticated.sql`` aplicadas.
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
async def test_authenticated_sem_insert_update_delete_em_documento_normativo(pg_conn) -> None:
    """Após REVOKE (0037), ``authenticated`` só deve poder SELECT na tabela RAG-light."""
    reg = await pg_conn.fetchval("SELECT to_regclass('qdi_rag.documento_normativo')::text")
    if not reg:
        pytest.skip("Tabela qdi_rag.documento_normativo ausente (extensão vector / migração 0020)")

    for priv in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
        tem = await pg_conn.fetchval(
            "SELECT has_table_privilege('authenticated', 'qdi_rag.documento_normativo', $1)",
            priv,
        )
        assert tem is False, f"authenticated não deve ter {priv} em documento_normativo (H-003)"

    pode_select = await pg_conn.fetchval(
        "SELECT has_table_privilege('authenticated', 'qdi_rag.documento_normativo', 'SELECT')",
    )
    assert pode_select is True
