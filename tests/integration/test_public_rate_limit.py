"""Teste de rate limit em rotas públicas (middleware em memória)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import get_settings


@pytest.fixture
def app_limitado(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("QDI_PUBLIC_RATE_LIMIT_PER_MINUTE", "2")
    monkeypatch.setenv("QDI_PUBLIC_RATE_LIMIT_ENABLED", "true")
    get_settings.cache_clear()
    from src.presentation.api.middleware import public_rate_limit as prl

    prl._contagens.clear()
    from src.presentation.api.main import create_app

    app = create_app()
    yield app
    prl._contagens.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_normativa_retorna_429_apos_limite(app_limitado) -> None:
    transport = ASGITransport(app=app_limitado)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(2):
            r = await client.post("/normativa/validar-ancora", json={"texto": "LC 214/2025 art. 1"})
            assert r.status_code == 200
        r3 = await client.post("/normativa/validar-ancora", json={"texto": "LC 214/2025 art. 1"})
        assert r3.status_code == 429
        assert r3.headers.get("Retry-After") == "60"
