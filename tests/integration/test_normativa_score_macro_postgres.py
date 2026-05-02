"""
Integração PostgreSQL — pesos macro versionados (migração 0015).

Requer Postgres acessível (`make dev` ou `QDI_POSTGRES_TEST_URL`).
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import psycopg2
import pytest

from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)


@pytest.fixture(scope="module")
def dsn_com_migracao_0015() -> str:
    try:
        conn = psycopg2.connect(POSTGRES_URL, connect_timeout=4)
    except Exception:
        pytest.skip("PostgreSQL indisponível — suba `make dev` ou defina QDI_POSTGRES_TEST_URL")
    mig = (
        Path(__file__).resolve().parents[2]
        / "src/infrastructure/db/migrations/0015_normativa_score_macro_dimensao.sql"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(mig.read_text(encoding="utf-8"))
        conn.commit()
        yield POSTGRES_URL
    finally:
        conn.close()


@pytest.mark.postgres
def test_repo_retorna_sete_dimensoes_pos_migracao(dsn_com_migracao_0015: str) -> None:
    repo = PostgresNormativaScoreMacroRepository(dsn=dsn_com_migracao_0015)
    m = repo.obter_pesos_macro_validos_na_data(date(2026, 5, 1))
    assert len(m) == 7
    assert m[Dimensao.FISCAL] == 1.5
    assert m[Dimensao.COMPLIANCE_ABNT] == 1.2
