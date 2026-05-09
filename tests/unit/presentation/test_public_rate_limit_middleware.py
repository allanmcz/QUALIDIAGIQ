"""Testes unitários — ``PublicRateLimitMiddleware`` (ramos curtos e grupos de rota)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.presentation.api.middleware import public_rate_limit as prl
from src.presentation.api.middleware.public_rate_limit import PublicRateLimitMiddleware


@pytest.fixture(autouse=True)
def limpa_bucket_public_rl() -> None:
    """Evita vazamento de contadores entre testes."""
    prl._contagens.clear()
    yield
    prl._contagens.clear()


def _scope(
    method: str,
    path: str,
    *,
    client: tuple[str, int] | None = ("10.0.0.1", 4444),
) -> dict[str, object]:
    scope: dict[str, object] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("test", 80),
    }
    if client is not None:
        scope["client"] = client
    return scope


@pytest.mark.asyncio
async def test_desabilitado_passa_sem_contagem() -> None:
    mw = PublicRateLimitMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(_scope("GET", "/normativa/x"), receive)
    fake = MagicMock(public_rate_limit_enabled=False, public_rate_limit_per_minute=999)
    with patch.object(prl, "get_settings", return_value=fake):
        resp = await mw.dispatch(req, call_next)
    assert resp.body == b"ok"
    assert len(prl._contagens) == 0


@pytest.mark.asyncio
async def test_options_nao_entra_no_bucket() -> None:
    mw = PublicRateLimitMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"opt")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(_scope("OPTIONS", "/normativa/x"), receive)
    fake = MagicMock(public_rate_limit_enabled=True, public_rate_limit_per_minute=1)
    with patch.object(prl, "get_settings", return_value=fake):
        resp = await mw.dispatch(req, call_next)
    assert resp.body == b"opt"
    assert len(prl._contagens) == 0


@pytest.mark.asyncio
async def test_rota_fora_do_grupo_nao_conta() -> None:
    mw = PublicRateLimitMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"x")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(_scope("GET", "/health"), receive)
    fake = MagicMock(public_rate_limit_enabled=True, public_rate_limit_per_minute=1)
    with patch.object(prl, "get_settings", return_value=fake):
        resp = await mw.dispatch(req, call_next)
    assert resp.body == b"x"
    assert len(prl._contagens) == 0


@pytest.mark.asyncio
async def test_public_institucional_ip_unknown_quando_sem_client() -> None:
    """``request.client`` ausente → IP ``unknown`` (ramo defensivo)."""
    mw = PublicRateLimitMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"x")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope("GET", "/public/institucional", client=None)
    req = Request(scope, receive)
    fake = MagicMock(public_rate_limit_enabled=True, public_rate_limit_per_minute=5)
    with patch.object(prl, "get_settings", return_value=fake):
        await mw.dispatch(req, call_next)

    assert any(
        ip == "unknown" and grupo == "public_institucional" for ip, _, grupo in prl._contagens
    )


@pytest.mark.asyncio
async def test_supera_limite_retorna_429_com_retry_after() -> None:
    mw = PublicRateLimitMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(_scope("GET", "/public/institucional"), receive)
    fake = MagicMock(public_rate_limit_enabled=True, public_rate_limit_per_minute=1)
    with patch.object(prl, "get_settings", return_value=fake):
        r1 = await mw.dispatch(req, call_next)
        r2 = await mw.dispatch(req, call_next)
    assert r1.status_code == 200
    assert r2.status_code == 429
    assert r2.headers.get("retry-after") == "60"
