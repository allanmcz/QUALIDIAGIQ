"""
Smoke integrado — migrações 0043–0045 e leitura pública com narrativa LLM.

Requer Postgres local (`make dev` / `make migrate`).
Variável: QDI_POSTGRES_TEST_URL (default :60322).
"""

from __future__ import annotations

import json
import os
import uuid

import httpx
import pytest

from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    buscar_diagnostico_conclusao_publica_sync,
    inserir_leitura_publica_self_service_sync,
)

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)
API_BASE = os.environ.get("QDI_API_BASE_URL", "http://127.0.0.1:60000")


@pytest.fixture
async def pg_conn():
    import asyncpg

    try:
        conn = await asyncpg.connect(POSTGRES_URL, timeout=5)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev`")
    try:
        yield conn
    finally:
        await conn.close()


@pytest.mark.asyncio
@pytest.mark.postgres
@pytest.mark.mvp_gate
async def test_schema_explicacao_llm_0043_0044_0045(pg_conn) -> None:
    """Coluna JSONB + histórico append-only + ledger de quota."""
    col = await pg_conn.fetchval(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'diagnosticos'
          AND column_name = 'explicacao_score_llm'
        """
    )
    assert col == 1
    hist = await pg_conn.fetchval(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'diagnostico_explicacao_score_llm_historico'
        """
    )
    assert hist == 1
    ledger = await pg_conn.fetchval(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'llm_tenant_usage_ledger'
        """
    )
    assert ledger == 1


@pytest.mark.postgres
@pytest.mark.mvp_gate
def test_conclusao_publica_retorna_texto_explicacao_llm() -> None:
    """Fluxo token + SELECT com explicacao_score_llm (C — self-service)."""
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    snap = {
        "text": "Narrativa smoke integração — dimensão fiscal.",
        "provider": "fake",
        "model": "fake-llm",
        "policy_version": "v",
        "blocked_by_guardrail": False,
    }
    import psycopg2

    conn = psycopg2.connect(POSTGRES_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnosticos (
                  id, tenant_id, respondente_email,
                  empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
                  empresa_cnae, empresa_uf, empresa_setor_macro,
                  status, plano, score_geral, criado_em, versao_otimista,
                  locale_relatorio, score_completo, explicacao_score_llm
                ) VALUES (
                  %s, %s, 'smoke-explic@teste.com',
                  '12345678000195', 'Smoke Explic LLM', 'micro', 'simples_nacional',
                  '1234567', 'SP', 'comercio',
                  'finalizado', 'gratuito', 55.0, now(), 1,
                  'pt-BR', %s::jsonb, %s::jsonb
                )
                """,
                (
                    str(diag_id),
                    str(tenant_id),
                    json.dumps(
                        {
                            "score_geral": {
                                "valor": 55.0,
                                "peso_total_aplicado": 1.0,
                                "perguntas_consideradas": [],
                            },
                            "score_por_dimensao": {},
                        }
                    ),
                    json.dumps(snap),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    token = inserir_leitura_publica_self_service_sync(POSTGRES_URL, diag_id, tenant_id)
    row = buscar_diagnostico_conclusao_publica_sync(
        POSTGRES_URL,
        diagnostico_id=diag_id,
        tenant_id_esperado=tenant_id,
        token_plain=token,
    )
    assert row is not None
    assert row.get("explicacao_score_llm") is not None
    expl = row["explicacao_score_llm"]
    if isinstance(expl, str):
        expl = json.loads(expl)
    assert expl["text"] == snap["text"]

    conn = psycopg2.connect(POSTGRES_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM diagnostico_leitura_publica_self_service WHERE diagnostico_id = %s",
                (str(diag_id),),
            )
            cur.execute("DELETE FROM diagnosticos WHERE id = %s", (str(diag_id),))
        conn.commit()
    finally:
        conn.close()


@pytest.mark.mvp_gate
def test_api_health_llm_responde() -> None:
    """GET /health/llm no API docker (E — governança)."""
    try:
        r = httpx.get(f"{API_BASE.rstrip('/')}/health/llm", timeout=5.0)
    except httpx.HTTPError:
        pytest.skip(f"API indisponível em {API_BASE} — suba `make dev`")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in ("ok", "degraded", "disabled")
