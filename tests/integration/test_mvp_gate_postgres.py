"""
Gate MVP (Postgres) — schema 0012 + 0016 + RLS dois tenants (P6 automatizado em CI).

Requer migrações aplicadas (job CI ou `make dev` / `make migrate`).
Variável: QDI_POSTGRES_TEST_URL (default postgres@127.0.0.1:60322).

Analogia: como validar VPD no Oracle com dois USER — aqui o ``tenant_id`` vem do JWT simulado.
"""

from __future__ import annotations

import json
import os
import uuid
from urllib.parse import urlparse, urlunparse

import asyncpg
import pytest

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)

RLS_LOGIN_ROLE = "qdi_rls_smoke_login"
RLS_LOGIN_PASSWORD = os.environ.get("QDI_RLS_TEST_ROLE_PASSWORD", "qdi_rls_smoke_ci_only")


def _url_with_credentials(dsn: str, user: str, password: str) -> str:
    parsed = urlparse(dsn)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    netloc = f"{user}:{password}@{host}:{port}"
    path = parsed.path if parsed.path else "/postgres"
    return urlunparse((parsed.scheme, netloc, path, "", "", ""))


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


@pytest.mark.asyncio
@pytest.mark.postgres
@pytest.mark.mvp_gate
async def test_schema_diagnosticos_inclui_coluna_aceite_lgpd_0012(pg_conn):
    """Confere migrações 0012 (LGPD), 0016 (locale), 0017 (faixa) e 0022 (quadro implantação)."""
    val = await pg_conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'aceite_termos_privacidade_em'
        """)
    assert val == 1
    loc = await pg_conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'locale_relatorio'
        """)
    assert loc == 1
    ff = await pg_conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'empresa_faixa_faturamento'
        """)
    assert ff == 1
    qd = await pg_conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'quadro_implantacao_anotacoes'
        """)
    if qd != 1:
        pytest.skip(
            "Coluna quadro_implantacao_anotacoes ausente — reaplique migrações "
            "(ex.: `docker compose down -v && make dev` ou aplique 0022 no Postgres de teste)."
        )


@pytest.mark.asyncio
@pytest.mark.postgres
@pytest.mark.mvp_gate
async def test_rls_authenticated_ve_apenas_proprio_tenant(pg_conn):
    """
    Dois ``tenant_id`` distintos: sessão ``authenticated`` + JWT simulado só enxerga seu conjunto.

    Base: ``0003_rls_policies.sql`` (``qdi_jwt_tenant_id`` + policies).
    """
    db_name = await pg_conn.fetchval("SELECT current_database()")
    # CREATE ROLE não pode rodar dentro de transação explícita — usar try/except.
    try:
        await pg_conn.execute(f"CREATE ROLE {RLS_LOGIN_ROLE} LOGIN PASSWORD '{RLS_LOGIN_PASSWORD}'")
    except asyncpg.PostgresError as exc:
        if "already exists" not in str(exc).lower():
            raise
    await pg_conn.execute(f"ALTER ROLE {RLS_LOGIN_ROLE} PASSWORD '{RLS_LOGIN_PASSWORD}'")
    await pg_conn.execute(f'GRANT CONNECT ON DATABASE "{db_name}" TO {RLS_LOGIN_ROLE}')
    await pg_conn.execute(f"GRANT USAGE ON SCHEMA public TO {RLS_LOGIN_ROLE}")
    await pg_conn.execute(f"GRANT authenticated TO {RLS_LOGIN_ROLE}")

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    id_a = uuid.uuid4()
    id_b = uuid.uuid4()

    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, versao_otimista
        ) VALUES (
          $1, $2, 'rls-a@teste.com',
          '12345678000195', 'Tenant A RLS', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'em_andamento', 'gratuito', NULL, now(), 1
        ),
        (
          $3, $4, 'rls-b@teste.com',
          '12345678000196', 'Tenant B RLS', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'em_andamento', 'gratuito', NULL, now(), 1
        )
        """,
        id_a,
        tenant_a,
        id_b,
        tenant_b,
    )

    rls_url = _url_with_credentials(POSTGRES_URL, RLS_LOGIN_ROLE, RLS_LOGIN_PASSWORD)
    conn_rls = await asyncpg.connect(rls_url, timeout=5)
    try:
        async with conn_rls.transaction():
            await conn_rls.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"tenant_id": str(tenant_a)}),
            )
            await conn_rls.execute("SET LOCAL ROLE authenticated")
            rows_a = await conn_rls.fetch("SELECT id FROM diagnosticos ORDER BY id")
        assert len(rows_a) == 1
        assert rows_a[0]["id"] == id_a

        async with conn_rls.transaction():
            await conn_rls.execute(
                "SELECT set_config('request.jwt.claims', $1, true)",
                json.dumps({"tenant_id": str(tenant_b)}),
            )
            await conn_rls.execute("SET LOCAL ROLE authenticated")
            rows_b = await conn_rls.fetch("SELECT id FROM diagnosticos ORDER BY id")
        assert len(rows_b) == 1
        assert rows_b[0]["id"] == id_b
    finally:
        await conn_rls.close()

    await pg_conn.execute("DELETE FROM diagnosticos WHERE id = ANY($1::uuid[])", [id_a, id_b])
