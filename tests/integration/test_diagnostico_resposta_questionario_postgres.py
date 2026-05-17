"""Integração PostgreSQL — respostas normalizadas (migration 0052)."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import asyncpg
import pytest

from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.application.services.diagnostico_resposta_materializacao import derivar_respostas_e_linhas
from src.domain.entities.questionario import Pergunta, TipoPergunta
from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.postgres_diagnostico_resposta_sync import (
    inserir_respostas_questionario_em_cursor,
    listar_respostas_questionario_sync,
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
    path = MIGRATIONS / "0052_diagnostico_resposta_questionario.sql"
    if path.exists():
        await conn.execute(path.read_text(encoding="utf-8"))
    try:
        yield conn
    finally:
        await conn.close()


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_insert_e_lista_respostas_ordenadas(pg_conn: asyncpg.Connection) -> None:
    """Persistência append-only e leitura por ordem_exibicao."""
    tid = uuid.uuid4()
    did = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em, versao_otimista
        ) VALUES (
          $1, $2, 'resp@teste.com',
          '12345678000195', 'RESP LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(), 1
        )
        ON CONFLICT (id) DO NOTHING
        """,
        did,
        tid,
    )
    pergunta = Pergunta(
        codigo="Q-FIS-INT-01",
        dimensao=Dimensao.FISCAL,
        texto="Pergunta integração",
        peso=3.0,
        tipo=TipoPergunta.TERNARIA,
        base_legal="LC 214/2025",
    )
    _, linhas = derivar_respostas_e_linhas(
        did,
        [EntradaRespostaDiagnostico(pergunta=pergunta, valor_bruto="sim")],
    )

    import psycopg2

    conn = psycopg2.connect(POSTGRES_URL.replace("+asyncpg", ""))
    try:
        with conn.cursor() as cur:
            inserir_respostas_questionario_em_cursor(cur, did, tid, linhas)
        conn.commit()
    finally:
        conn.close()

    dsn = POSTGRES_URL.replace("postgresql+asyncpg://", "postgresql://")
    itens = listar_respostas_questionario_sync(dsn, did, tid)
    assert len(itens) == 1
    assert itens[0]["pergunta_codigo"] == "Q-FIS-INT-01"
    assert itens[0]["valor_exibicao"] == "Sim"


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_worm_bloqueia_update_resposta(pg_conn: asyncpg.Connection) -> None:
    """Respostas do questionário são append-only."""
    tid = uuid.uuid4()
    did = uuid.uuid4()
    rid = uuid.uuid4()
    await pg_conn.execute(
        """
        INSERT INTO diagnosticos (
          id, tenant_id, respondente_email,
          empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
          empresa_cnae, empresa_uf, empresa_setor_macro,
          status, plano, score_geral, criado_em, finalizado_em, versao_otimista
        ) VALUES (
          $1, $2, 'worm@teste.com',
          '12345678000195', 'WORM LTDA', 'micro', 'simples_nacional',
          '1234567', 'SP', 'comercio',
          'finalizado', 'gratuito', 50.0, now(), now(), 1
        )
        ON CONFLICT (id) DO NOTHING
        """,
        did,
        tid,
    )
    await pg_conn.execute(
        """
        INSERT INTO diagnostico_resposta_questionario (
          id, diagnostico_id, tenant_id, ordem_exibicao,
          pergunta_id, pergunta_codigo, dimensao, tipo_pergunta,
          texto_pergunta, peso, valor_bruto, valor_exibicao, excluida_calculo
        ) VALUES (
          $1, $2, $3, 0,
          $4, 'Q-X-001', 'fiscal', 'ternaria',
          'Texto', 1.0, '"sim"'::jsonb, 'Sim', false
        )
        """,
        rid,
        did,
        tid,
        uuid.uuid4(),
    )
    with pytest.raises(Exception, match="append-only"):
        await pg_conn.execute(
            "UPDATE diagnostico_resposta_questionario SET valor_exibicao = 'X' WHERE id = $1",
            rid,
        )
