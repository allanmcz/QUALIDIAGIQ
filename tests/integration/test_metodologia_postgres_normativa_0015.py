"""
Integração: GET /metodologia e /manifesto-pesos com pesos macro lidos do Postgres (migração 0015).

Requer PostgreSQL acessível e migração ``0015_normativa_score_macro_dimensao`` aplicada.
CI e ``make ci-integration`` já aplicam todas as migrações antes dos testes.

Variáveis: ``QDI_POSTGRES_TEST_URL`` ou default ``127.0.0.1:60322``; define ``DATABASE_URL`` só no âmbito do teste.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from src.presentation.api.main import app

POSTGRES_SYNC = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)

SEED_MACRO_0015 = {
    "fiscal": 1.5,
    "tecnologica": 1.3,
    "compliance_abnt_17301": 1.2,
    "estrategica": 1.0,
    "contabil": 1.0,
    "financeira": 1.0,
    "operacional": 1.0,
}


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.postgres
async def test_metodologia_manifesto_pesos_macros_coerentes_com_seed_0015(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    try:
        conn = await asyncpg.connect(POSTGRES_SYNC, timeout=5)
    except Exception:
        pytest.skip("PostgreSQL indisponível — defina QDI_POSTGRES_TEST_URL ou suba o compose.")

    try:
        n = await conn.fetchval("""
            SELECT count(DISTINCT dimensao)::int
            FROM qdi.normativa_score_macro_dimensao
            WHERE vigencia_fim IS NULL
        """)
    finally:
        await conn.close()

    if n != 7:
        pytest.skip("Tabela normativa 0015 ausente ou incompleta (esperadas 7 dimensões ativas).")

    dsn_async = POSTGRES_SYNC.replace("postgresql://", "postgresql+asyncpg://", 1)
    monkeypatch.setenv("DATABASE_URL", dsn_async)

    r1 = await async_client.get("/diagnosticos/metodologia")
    assert r1.status_code == 200
    body = r1.json()
    macros = body["pesos_macro_dimensao_score_geral"]
    assert set(macros.keys()) == set(SEED_MACRO_0015.keys())
    for k, v in SEED_MACRO_0015.items():
        assert pytest.approx(float(macros[k]), rel=0, abs=0.001) == v

    r2 = await async_client.get("/diagnosticos/manifesto-pesos")
    assert r2.status_code == 200
    man = r2.json()["pesos_macro_dimensao"]
    for k, v in SEED_MACRO_0015.items():
        assert pytest.approx(float(man[k]), rel=0, abs=0.001) == v
