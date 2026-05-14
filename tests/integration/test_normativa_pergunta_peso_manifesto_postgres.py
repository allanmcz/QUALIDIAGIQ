"""
Integração: linha em ``qdi.normativa_pergunta_peso`` (0042) + GET ``/diagnosticos/manifesto-pesos``.

Requer PostgreSQL acessível e migração 0042 aplicada (``make dev`` / ``make migrate`` ou CI).

Variável: ``QDI_POSTGRES_TEST_URL`` ou default ``127.0.0.1:60322``.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import get_settings
from src.infrastructure.questionario.banco_cache import reset_catalogo_perguntas_em_memoria
from src.presentation.api.main import app

POSTGRES_SYNC = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)

ROTULO_TESTE = "integration-0042-qdi-manifesto-pergunta"
# Código presente em ``perguntas_mvp.json`` (peso catálogo 7.5 no MVP).
CODIGO_PERGUNTA = "Q-EST-001"

PESO_CATALOGO_JSON = 7.5
PESO_NORMATIVO_DB = 12.34


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestNormativaPerguntaPesoManifestoPostgres:
    """Integração: overlay ``0042`` + endpoint público de manifesto de pesos."""

    @pytest.mark.asyncio
    @pytest.mark.postgres
    async def test_manifesto_pesos_overlay_apos_insert_0042(
        self,
        async_client: AsyncClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Insere overlay vigente, invalida cache do catálogo e valida ``normativa_overlay`` no manifesto.

        LC 214/2025 — transparência; ABNT NBR 17301:2026 — rastreabilidade metodológica.
        """
        try:
            conn = await asyncpg.connect(POSTGRES_SYNC, timeout=5)
        except Exception:
            pytest.skip("PostgreSQL indisponível — defina QDI_POSTGRES_TEST_URL ou suba o compose.")

        try:
            tbl = await conn.fetchval("""
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'qdi' AND table_name = 'normativa_pergunta_peso'
            """)
            if tbl != 1:
                pytest.skip("Tabela qdi.normativa_pergunta_peso ausente (aplique migração 0042).")

            await conn.execute(
                "DELETE FROM qdi.normativa_pergunta_peso WHERE rotulo_versao = $1",
                ROTULO_TESTE,
            )
            await conn.execute(
                """
                INSERT INTO qdi.normativa_pergunta_peso
                    (pergunta_codigo, vigencia_inicio, vigencia_fim, peso, rotulo_versao)
                VALUES ($1, DATE '2020-01-01', NULL, $2::numeric, $3)
                """,
                CODIGO_PERGUNTA,
                str(PESO_NORMATIVO_DB),
                ROTULO_TESTE,
            )
        finally:
            await conn.close()

        dsn_async = POSTGRES_SYNC.replace("postgresql://", "postgresql+asyncpg://", 1)
        monkeypatch.setenv("DATABASE_URL", dsn_async)
        get_settings.cache_clear()
        reset_catalogo_perguntas_em_memoria()

        try:
            r = await async_client.get("/diagnosticos/manifesto-pesos")
            assert r.status_code == 200, r.text
            perguntas = r.json()["perguntas"]
            item = next((p for p in perguntas if p["codigo"] == CODIGO_PERGUNTA), None)
            assert item is not None, "pergunta Q-EST-001 deve existir no manifesto"

            assert pytest.approx(float(item["peso"]), rel=0, abs=0.001) == PESO_NORMATIVO_DB
            ov = item.get("normativa_overlay")
            assert ov is not None
            assert (
                pytest.approx(float(ov["peso_catalogo_json"]), rel=0, abs=0.001)
                == PESO_CATALOGO_JSON
            )
            assert (
                pytest.approx(float(ov["peso_normativo_db"]), rel=0, abs=0.001) == PESO_NORMATIVO_DB
            )
            assert ov["vigencia_inicio"] == "2020-01-01"
            assert ov["vigencia_fim"] is None
            assert ov["rotulo_versao"] == ROTULO_TESTE
        finally:
            get_settings.cache_clear()
            reset_catalogo_perguntas_em_memoria()
            conn_del = await asyncpg.connect(POSTGRES_SYNC, timeout=5)
            try:
                await conn_del.execute(
                    "DELETE FROM qdi.normativa_pergunta_peso WHERE rotulo_versao = $1",
                    ROTULO_TESTE,
                )
            finally:
                await conn_del.close()
