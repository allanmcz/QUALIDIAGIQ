"""Testes do rate limit de rotas sensíveis (ADR-020 / QDI-H-034)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import get_settings
from src.presentation.api.middleware.sensitive_route_rate_limit import (
    SensitiveRouteRateLimitMiddleware,
    _grupo_rota_sensivel,
)


class TestGrupoRotaSensivel:
    """Mapeamento método + path → bucket de quota."""

    def test_post_login_entra_no_grupo(self) -> None:
        assert _grupo_rota_sensivel("POST", "/auth/login") == "sensivel_auth_login"

    def test_post_login_com_barra_final(self) -> None:
        assert _grupo_rota_sensivel("POST", "/auth/login/") == "sensivel_auth_login"

    def test_get_login_ignorado(self) -> None:
        assert _grupo_rota_sensivel("GET", "/auth/login") is None

    def test_post_cadastro(self) -> None:
        assert _grupo_rota_sensivel("POST", "/auth/cadastro") == "sensivel_auth_cadastro"

    def test_post_verificar_email_solicitar(self) -> None:
        assert (
            _grupo_rota_sensivel("POST", "/auth/verificar-email/solicitar")
            == "sensivel_auth_otp_solicitar"
        )

    def test_post_verificar_email_confirmar(self) -> None:
        assert (
            _grupo_rota_sensivel("POST", "/auth/verificar-email/confirmar")
            == "sensivel_auth_otp_confirmar"
        )

    def test_post_rascunho_self_service(self) -> None:
        assert (
            _grupo_rota_sensivel("POST", "/diagnosticos/rascunho-self-service")
            == "sensivel_diag_rascunho_ss"
        )

    def test_post_rascunho_self_service_subpath(self) -> None:
        assert (
            _grupo_rota_sensivel("POST", "/diagnosticos/rascunho-self-service/concluir")
            == "sensivel_diag_rascunho_ss"
        )

    def test_post_diagnosticos_fora_do_prefixo_nao_sensivel(self) -> None:
        assert _grupo_rota_sensivel("POST", "/diagnosticos/outro") is None


@pytest.mark.asyncio
async def test_options_nao_conta_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPTIONS deve passar sem aplicar rate limit."""
    import src.presentation.api.middleware.sensitive_route_rate_limit as mod_lim

    mod_lim._contagens.clear()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()

    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(SensitiveRouteRateLimitMiddleware)

    @app.post("/auth/login")
    async def _login() -> dict[str, str]:
        return {"ok": "true"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(10):
            r = await client.request("OPTIONS", "/auth/login")
            assert r.status_code in (200, 405)

    mod_lim._contagens.clear()
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_nao_conta_quota(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET fora do grupo não dispara contagem."""
    import src.presentation.api.middleware.sensitive_route_rate_limit as mod_lim

    mod_lim._contagens.clear()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_PER_MINUTE", "1")
    get_settings.cache_clear()

    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(SensitiveRouteRateLimitMiddleware)

    @app.get("/healthz")
    async def _h() -> dict[str, str]:
        return {"ok": "1"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            r = await client.get("/healthz")
            assert r.status_code == 200

    mod_lim._contagens.clear()
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_dispatch_sem_cliente_usa_unknown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quando ``request.client`` é None, a quota usa o host «unknown»."""
    from unittest.mock import AsyncMock, MagicMock

    import src.presentation.api.middleware.sensitive_route_rate_limit as mod_lim

    mod_lim._contagens.clear()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_PER_MINUTE", "5")
    get_settings.cache_clear()

    from starlette.applications import Starlette

    starlette_app = Starlette()
    mw = SensitiveRouteRateLimitMiddleware(starlette_app)
    req = MagicMock()
    req.method = "POST"
    req.url.path = "/auth/login"
    req.client = None
    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    await mw.dispatch(req, call_next)
    assert call_next.await_count == 1

    mod_lim._contagens.clear()
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_middleware_desligado_nao_limita(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com QDI_SENSITIVE_RATE_LIMIT_ENABLED=false, não devolve 429."""
    import src.presentation.api.middleware.sensitive_route_rate_limit as mod_lim

    mod_lim._contagens.clear()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()

    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(SensitiveRouteRateLimitMiddleware)

    @app.post("/auth/login")
    async def _login() -> dict[str, str]:
        return {"ok": "true"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(12):
            r = await client.post("/auth/login")
            assert r.status_code == 200

    mod_lim._contagens.clear()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_sexto_post_login_retorna_429(monkeypatch: pytest.MonkeyPatch) -> None:
    """Após N POST/min/IP (default 5), o 6.º pedido recebe 429."""
    import src.presentation.api.middleware.sensitive_route_rate_limit as mod_lim

    mod_lim._contagens.clear()
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_PER_MINUTE", "5")
    get_settings.cache_clear()

    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(SensitiveRouteRateLimitMiddleware)

    @app.post("/auth/login")
    async def _login() -> dict[str, str]:
        return {"ok": "true"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            r = await client.post("/auth/login")
            assert r.status_code == 200
        r6 = await client.post("/auth/login")
        assert r6.status_code == 429
        assert "Retry-After" in r6.headers

    mod_lim._contagens.clear()
    monkeypatch.setenv("QDI_SENSITIVE_RATE_LIMIT_ENABLED", "false")
    get_settings.cache_clear()
