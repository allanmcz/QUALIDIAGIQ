"""
Integração PostgreSQL — trigger WORM granular (migração 0006).

Requer instância com migrações aplicadas (`make dev` ou `make migrate`).
Variável opcional: QDI_POSTGRES_TEST_URL (default postgres@127.0.0.1:60322).
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import asyncpg
import pytest

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


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_worm_bloqueia_mutacao_de_evidence_pos_finalizado(pg_conn):
    """UPDATE de score após finalizado deve falhar; URL do PDF + versão pode progredir."""
    # Garante função granular (0006) mesmo em volumes Docker criados só com 0005.
    mig_0006 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0006_worm_column_granular.sql"
    )
    mig_0011 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0011_checklist_m12_autoconf.sql"
    )
    mig_0012 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0012_aceite_lgpd_e_worm.sql"
    )
    mig_0025 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0025_worm_permite_reatribuir_tenant_vinculo_lead.sql"
    )
    await pg_conn.execute(mig_0006.read_text(encoding="utf-8"))
    await pg_conn.execute(mig_0011.read_text(encoding="utf-8"))
    await pg_conn.execute(mig_0012.read_text(encoding="utf-8"))
    if mig_0025.exists():
        await pg_conn.execute(mig_0025.read_text(encoding="utf-8"))

    tid = uuid.uuid4()
    did = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em,
          versao_otimista
        ) VALUES (
          $1, $2, 'worm@teste.com',
          '12345678000195', 'WORM LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(),
          1
        )
        """,
        did,
        tid,
    )

    with pytest.raises(asyncpg.PostgresError) as excinfo:
        await pg_conn.execute(
            "UPDATE diagnosticos SET score_geral = 99.0 WHERE id = $1",
            did,
        )
    msg = str(excinfo.value).lower()
    assert "worm" in msg or "evidência" in msg or "imutável" in msg

    await pg_conn.execute(
        """
        UPDATE diagnosticos
        SET relatorio_pdf_url = $2, versao_otimista = 2
        WHERE id = $1 AND versao_otimista = 1
        """,
        did,
        "https://exemplo/qdi-rel.pdf",
    )
    row = await pg_conn.fetchrow(
        "SELECT relatorio_pdf_url, versao_otimista FROM diagnosticos WHERE id = $1",
        did,
    )
    assert row is not None
    assert row["versao_otimista"] == 2
    assert row["relatorio_pdf_url"] == "https://exemplo/qdi-rel.pdf"

    m12_esperado = [True] + [False] * 9
    await pg_conn.execute(
        """
        UPDATE diagnosticos
        SET checklist_m12_estado = $2::jsonb, versao_otimista = 3
        WHERE id = $1 AND versao_otimista = 2
        """,
        did,
        json.dumps(m12_esperado),
    )
    row_m12 = await pg_conn.fetchrow(
        "SELECT checklist_m12_estado, versao_otimista FROM diagnosticos WHERE id = $1",
        did,
    )
    assert row_m12 is not None
    assert row_m12["versao_otimista"] == 3
    raw_m12 = row_m12["checklist_m12_estado"]
    if isinstance(raw_m12, str):
        raw_m12 = json.loads(raw_m12)
    assert raw_m12 == m12_esperado

    with pytest.raises(asyncpg.PostgresError) as exc_aceite:
        await pg_conn.execute(
            "UPDATE diagnosticos SET aceite_termos_privacidade_em = now() WHERE id = $1",
            did,
        )
    msg_aceite = str(exc_aceite.value).lower()
    assert "worm" in msg_aceite or "evidência" in msg_aceite or "imutável" in msg_aceite

    await pg_conn.execute("DELETE FROM diagnosticos WHERE id = $1", did)


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_worm_permite_reatribuir_tenant_id_pos_finalizado(pg_conn):
    """Mesmo finalizado, UPDATE só de tenant_id deve passar (vincular lead self-service)."""
    mig_0006 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0006_worm_column_granular.sql"
    )
    mig_0025 = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0025_worm_permite_reatribuir_tenant_vinculo_lead.sql"
    )
    await pg_conn.execute(mig_0006.read_text(encoding="utf-8"))
    if mig_0025.exists():
        await pg_conn.execute(mig_0025.read_text(encoding="utf-8"))

    tid_pool = uuid.uuid4()
    tid_dest = uuid.uuid4()
    did = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em,
          versao_otimista
        ) VALUES (
          $1, $2, 'lead@exemplo.com',
          '12345678000195', 'Lead SA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 40.0, now(), now(),
          1
        )
        """,
        did,
        tid_pool,
    )
    await pg_conn.execute(
        "UPDATE diagnosticos SET tenant_id = $2 WHERE id = $1",
        did,
        tid_dest,
    )
    row = await pg_conn.fetchrow("SELECT tenant_id FROM diagnosticos WHERE id = $1", did)
    assert row is not None
    assert row["tenant_id"] == tid_dest

    await pg_conn.execute("DELETE FROM diagnosticos WHERE id = $1", did)
