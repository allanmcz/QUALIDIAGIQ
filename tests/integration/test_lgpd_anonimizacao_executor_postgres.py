"""
Integração PostgreSQL — executor de anonimização LGPD (adapter síncrono + WORM 0029 + coluna IP 0036).

Requer instância com migrações aplicadas (`make dev` + `make migrate`) ou, no mínimo,
tabelas `diagnosticos`, `lgpd_titular_solicitacao` e ficheiros 0029/0036 para criar
`lgpd_anonimizacao_log`, função WORM e `respondente_ip_origem`.

Variável opcional: QDI_POSTGRES_TEST_URL (default postgres@127.0.0.1:60322).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import asyncpg
import pytest

from src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter import (
    PostgresLgpdAnonimizacaoExecutorAdapter,
)

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)


@pytest.fixture
async def pg_conn():
    try:
        conn = await asyncpg.connect(POSTGRES_URL, timeout=3)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev` ou defina QDI_POSTGRES_TEST_URL")
    try:
        yield conn
    finally:
        await conn.close()


async def _aplicar_migracao_0029(pg_conn: asyncpg.Connection) -> None:
    """Idempotente — garante tabela de log e ``CREATE OR REPLACE`` da função WORM com anonimização."""
    mig = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0029_lgpd_anonimizacao_log_worm.sql"
    )
    if not mig.exists():
        pytest.skip("Ficheiro de migração 0029 não encontrado.")
    await pg_conn.execute(mig.read_text(encoding="utf-8"))


async def _aplicar_migracao_0036(pg_conn: asyncpg.Connection) -> None:
    """Coluna respondente_ip_origem + função WORM alinhada ao anon IP (J2)."""
    mig = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0036_respondente_ip_origem_lgpd.sql"
    )
    if not mig.exists():
        pytest.skip("Ficheiro de migração 0036 não encontrado.")
    await pg_conn.execute(mig.read_text(encoding="utf-8"))


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_executor_anonimiza_respondente_e_conclui_solicitacao(pg_conn):
    """Fluxo feliz: diagnóstico finalizado + solicitação deferida → sentinelas + log + concluída."""
    await _aplicar_migracao_0029(pg_conn)
    await _aplicar_migracao_0036(pg_conn)

    tid = uuid.uuid4()
    did = uuid.uuid4()
    sid = uuid.uuid4()
    actor = uuid.uuid4()

    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email, respondente_nome, respondente_cargo,
          respondente_telefone, respondente_ip_origem,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em,
          versao_otimista
        ) VALUES (
          $1, $2, 'titular@antes.com', 'Nome Original', 'Cargo X',
          '11999998888', '203.0.113.10',
          '12345678000195', 'ANON DEMO LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(),
          1
        )
        """,
        did,
        tid,
    )

    await pg_conn.execute(
        """
        INSERT INTO lgpd_titular_solicitacao (
            id, tenant_id, diagnostico_id, tipo, status, canal, solicitante_email, payload
        ) VALUES ($1, $2, $3, 'anonimizacao', 'deferida', 'plataforma', 'titular@antes.com', '{}'::jsonb)
        """,
        sid,
        tid,
        did,
    )

    adapter = PostgresLgpdAnonimizacaoExecutorAdapter(dsn_sync=POSTGRES_URL)
    await adapter.aplicar_anonimizacao_respondente(
        tenant_id=tid,
        diagnostico_id=did,
        solicitacao_id=sid,
        actor_user_id=actor,
    )

    esperado_email = f"anon+{str(did).replace('-', '')}@invalid.qdi"
    row_d = await pg_conn.fetchrow(
        """
        SELECT respondente_email, respondente_nome, respondente_cargo, respondente_telefone,
               respondente_ip_origem
        FROM diagnosticos WHERE id = $1
        """,
        did,
    )
    assert row_d is not None
    assert row_d["respondente_email"] == esperado_email
    assert row_d["respondente_nome"] == "[anonimizado]"
    assert row_d["respondente_cargo"] is None
    assert row_d["respondente_telefone"] is None
    assert row_d["respondente_ip_origem"] is None

    row_s = await pg_conn.fetchrow(
        "SELECT status FROM lgpd_titular_solicitacao WHERE id = $1",
        sid,
    )
    assert row_s is not None
    assert str(row_s["status"]) == "concluida"

    n_log = await pg_conn.fetchval(
        "SELECT COUNT(*) FROM lgpd_anonimizacao_log WHERE diagnostico_id = $1 AND solicitacao_id = $2",
        did,
        sid,
    )
    assert n_log == 1

    await pg_conn.execute("DELETE FROM lgpd_titular_solicitacao WHERE id = $1", sid)
    await pg_conn.execute("DELETE FROM diagnosticos WHERE id = $1", did)
