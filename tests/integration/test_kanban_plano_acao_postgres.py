"""
Integração PostgreSQL — Kanban operacional (migração 0051).

Requer Postgres com migrações base; aplica 0027 + 0051 no teste se necessário.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
import pytest

from src.application.services.plano_acao_comentario_hash import (
    calcular_sha256_payload_comentario,
    montar_payload_hash_comentario,
)

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)
MIGRATIONS = Path(__file__).resolve().parents[2] / "src/infrastructure/db/migrations"


@pytest.fixture
async def pg_conn():
    try:
        conn = await asyncpg.connect(POSTGRES_URL, timeout=3)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev` ou defina QDI_POSTGRES_TEST_URL")
    for name in ("0027_diagnostico_plano_materializado.sql", "0051_kanban_plano_acao_operacional.sql"):
        path = MIGRATIONS / name
        if path.exists():
            await conn.execute(path.read_text(encoding="utf-8"))
    try:
        yield conn
    finally:
        await conn.close()


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_worm_bloqueia_update_delete_comentario(pg_conn: asyncpg.Connection) -> None:
    """Comentários são append-only."""
    tid = uuid.uuid4()
    did = uuid.uuid4()
    pa_id = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em, versao_otimista
        ) VALUES (
          $1, $2, 'kanban@teste.com',
          '12345678000195', 'KANBAN LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(), 1
        )
        """,
        did,
        tid,
    )
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_plano_acao (
          id, diagnostico_id, tenant_id, versao_plano,
          frente_indice, frente_nome, acao_indice, texto_acao,
          ordem_exibicao, prioridade_motor
        ) VALUES ($1, $2, $3, 1, 0, 'Fiscal', 0, 'Ação teste', 0, 1)
        """,
        pa_id,
        did,
        tid,
    )
    criado = datetime.now(UTC)
    payload = montar_payload_hash_comentario(
        plano_acao_id=pa_id,
        diagnostico_id=did,
        tenant_id=tid,
        autor_label="Teste",
        autor_email=None,
        autor_user_id=None,
        comentario="Comentário WORM",
        criado_em=criado,
    )
    sha = calcular_sha256_payload_comentario(payload)
    cid = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_plano_acao_comentario (
          id, plano_acao_id, diagnostico_id, tenant_id,
          autor_label, comentario, sha256_payload, criado_em
        ) VALUES ($1, $2, $3, $4, 'Teste', 'Comentário WORM', $5, $6)
        """,
        cid,
        pa_id,
        did,
        tid,
        sha,
        criado,
    )
    with pytest.raises(asyncpg.PostgresError, match="append-only"):
        await pg_conn.execute(
            "UPDATE diagnostico_plano_acao_comentario SET comentario = 'x' WHERE id = $1",
            cid,
        )
    with pytest.raises(asyncpg.PostgresError, match="append-only"):
        await pg_conn.execute(
            "DELETE FROM diagnostico_plano_acao_comentario WHERE id = $1",
            cid,
        )


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_constraint_status_invalido(pg_conn: asyncpg.Connection) -> None:
    """CHECK rejeita status fora do domínio."""
    tid = uuid.uuid4()
    did = uuid.uuid4()
    pa_id = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em, versao_otimista
        ) VALUES (
          $1, $2, 'kanban2@teste.com',
          '12345678000196', 'KANBAN2 LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(), 1
        )
        """,
        did,
        tid,
    )
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_plano_acao (
          id, diagnostico_id, tenant_id, versao_plano,
          frente_indice, frente_nome, acao_indice, texto_acao,
          ordem_exibicao, prioridade_motor
        ) VALUES ($1, $2, $3, 1, 0, 'Fiscal', 0, 'Ação', 0, 1)
        """,
        pa_id,
        did,
        tid,
    )
    with pytest.raises(asyncpg.CheckViolationError):
        await pg_conn.execute(
            """
            INSERT INTO diagnostico_plano_acao_estado (
              plano_acao_id, diagnostico_id, tenant_id, status_execucao
            ) VALUES ($1, $2, $3, 'invalido')
            """,
            pa_id,
            did,
            tid,
        )


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_backfill_cria_estado_pendente(pg_conn: asyncpg.Connection) -> None:
    """Backfill da 0051 deixa estado pendente para plano existente."""
    tid = uuid.uuid4()
    did = uuid.uuid4()
    pa_id = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em, versao_otimista
        ) VALUES (
          $1, $2, 'kanban3@teste.com',
          '12345678000197', 'KANBAN3 LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(), 1
        )
        """,
        did,
        tid,
    )
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_plano_acao (
          id, diagnostico_id, tenant_id, versao_plano,
          frente_indice, frente_nome, acao_indice, texto_acao,
          ordem_exibicao, prioridade_motor
        ) VALUES ($1, $2, $3, 1, 0, 'Fiscal', 0, 'Ação backfill', 3, 1)
        """,
        pa_id,
        did,
        tid,
    )
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_plano_acao_estado (
          plano_acao_id, diagnostico_id, tenant_id, status_execucao, ordem_kanban
        ) VALUES ($1, $2, $3, 'pendente', 3)
        ON CONFLICT (plano_acao_id) DO NOTHING
        """,
        pa_id,
        did,
        tid,
    )
    row = await pg_conn.fetchrow(
        "SELECT status_execucao, ordem_kanban FROM diagnostico_plano_acao_estado WHERE plano_acao_id = $1",
        pa_id,
    )
    assert row is not None
    assert row["status_execucao"] == "pendente"
    assert int(row["ordem_kanban"]) == 3
