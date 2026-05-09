"""Testes — ``TraceContextMiddleware`` (trace HTTP + ramo OpenTelemetry)."""

from __future__ import annotations

import base64
import json
import logging
import uuid
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from src.presentation.api.middleware.trace_context import TraceContextMiddleware


def _b64url_payload(d: dict[str, object]) -> str:
    raw = json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _scope_com_auth(trace: str, bearer_token: str | None) -> dict[str, object]:
    headers: list[tuple[bytes, bytes]] = [(b"x-trace-id", trace.encode())]
    if bearer_token:
        headers.append((b"authorization", bearer_token.encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/health",
        "raw_path": b"/health",
        "query_string": b"",
        "headers": headers,
        "scheme": "http",
        "server": ("test", 80),
        "client": ("127.0.0.1", 5555),
    }


@pytest.mark.asyncio
async def test_otel_span_recebe_trace_id_e_tenant_do_jwt() -> None:
    mw = TraceContextMiddleware(MagicMock())
    tid = str(uuid.uuid4())
    token = f"h.{_b64url_payload({'tenant_id': tid, 'sub': 'usr'})}.s"

    span = MagicMock()
    span.is_recording.return_value = True

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover — ASGI mínimo
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-fixo-1", f"Bearer {token}")
    req = Request(scope, receive)

    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-fixo-1"
    keys = [c.args[0] for c in span.set_attribute.call_args_list]
    assert "qualidiagiq.trace_id_http" in keys
    assert "tenant_id" in keys


@pytest.mark.asyncio
async def test_otel_claim_invalido_regista_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Payload JWT intermediário ilegível → except explícito + log de aviso."""
    mw = TraceContextMiddleware(MagicMock())
    span = MagicMock()
    span.is_recording.return_value = True

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    token = "Bearer a.!!!não-base64!!!.c"
    scope = _scope_com_auth("trace-warn", token)
    req = Request(scope, receive)

    caplog.set_level(logging.WARNING)
    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-warn"
    assert any("otel_tenant_claim_decode_falhou" in r.getMessage() for r in caplog.records)
