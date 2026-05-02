"""
Testes HTTP — GET /referencia/cnae/subclasses (M01 + P6/G2).

Endpoint público (somente leitura); DATABASE_URL + migrações 0013/0014 para 200 com dados.
"""

from __future__ import annotations

import os

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import get_settings
from src.presentation.api.main import app

POSTGRES_URL = os.environ.get(
    "QDI_POSTGRES_TEST_URL",
    "postgresql://postgres:postgres@127.0.0.1:60322/postgres",
)


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestCnaeReferenciaApi:
    @pytest.mark.asyncio
    async def test_sem_bearer_nao_retorna_401(self, async_client: AsyncClient) -> None:
        r = await async_client.get("/referencia/cnae/subclasses?q=6201")
        assert r.status_code != 401, r.text

    @pytest.mark.asyncio
    async def test_sem_database_url_retorna_503(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()
        try:
            r = await async_client.get("/referencia/cnae/subclasses?q=6201")
            assert r.status_code == 503
            det = r.json().get("detail", "")
            texto = det if isinstance(det, str) else str(det)
            assert "DATABASE_URL" in texto
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_consulta_curta_retorna_422(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)
        get_settings.cache_clear()
        try:
            r = await async_client.get("/referencia/cnae/subclasses?q=6")
            assert r.status_code == 422
        finally:
            get_settings.cache_clear()

    @pytest.mark.asyncio
    async def test_com_postgres_e_cnae_retorna_200(
        self, async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)
        get_settings.cache_clear()
        try:
            try:
                conn = await asyncpg.connect(POSTGRES_URL, timeout=3)
                await conn.fetchval("SELECT 1 FROM qdi.cnae_subclasse LIMIT 1")
                await conn.close()
            except Exception:
                pytest.skip("Postgres ou tabela qdi.cnae_subclasse indisponível")
            r = await async_client.get("/referencia/cnae/subclasses?q=6201&limite=5")
            assert r.status_code == 200
            body = r.json()
            assert "itens" in body
            assert isinstance(body["itens"], list)
            assert len(body["itens"]) >= 1
            assert body["itens"][0]["subclasse_id"]
            assert body["itens"][0]["descricao"]
        finally:
            get_settings.cache_clear()
