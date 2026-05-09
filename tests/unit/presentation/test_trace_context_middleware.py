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


@pytest.mark.asyncio
async def test_otel_desligado_nao_toca_span() -> None:
    mw = TraceContextMiddleware(MagicMock())

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-sem-otel", "Bearer x.y.z")
    req = Request(scope, receive)

    with patch(
        "src.presentation.api.middleware.trace_context.get_settings",
        return_value=MagicMock(otel_tracing_enabled=False),
    ):
        spy = MagicMock()
        with patch("opentelemetry.trace.get_current_span", spy):
            resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-sem-otel"
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_otel_span_nao_gravando_nao_seta_atributos() -> None:
    mw = TraceContextMiddleware(MagicMock())
    tid = str(uuid.uuid4())
    token = f"h.{_b64url_payload({'tenant_id': tid, 'sub': 'usr'})}.s"
    span = MagicMock()
    span.is_recording.return_value = False

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-no-record", f"Bearer {token}")
    req = Request(scope, receive)

    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-no-record"
    span.set_attribute.assert_not_called()


@pytest.mark.asyncio
async def test_otel_sem_tenant_id_no_payload_nao_seta_tenant_span() -> None:
    mw = TraceContextMiddleware(MagicMock())
    token = f"h.{_b64url_payload({'sub': 'so-sub'})}.s"
    span = MagicMock()
    span.is_recording.return_value = True

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-sem-tenant-claim", f"Bearer {token}")
    req = Request(scope, receive)

    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-sem-tenant-claim"
    keys = [c.args[0] for c in span.set_attribute.call_args_list]
    assert "qualidiagiq.trace_id_http" in keys
    assert "tenant_id" not in keys


@pytest.mark.asyncio
async def test_otel_excecao_generica_engole_sem_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Erros fora do tuple documentado → ``except Exception: pass`` (não quebra resposta)."""
    mw = TraceContextMiddleware(MagicMock())
    tid = str(uuid.uuid4())
    token = f"h.{_b64url_payload({'tenant_id': tid, 'sub': 'usr'})}.s"
    span = MagicMock()
    span.is_recording.return_value = True
    span.set_attribute.side_effect = RuntimeError("falha OTEL fictícia")

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-exc-generica", f"Bearer {token}")
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

    assert resp.headers["X-Trace-Id"] == "trace-exc-generica"
    assert not any("otel_tenant_claim_decode_falhou" in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_otel_sem_authorization_so_propaga_trace_no_span_tenant() -> None:
    """Com OTEL ativo, sem ``Authorization`` não tenta decodificar JWT no span."""
    mw = TraceContextMiddleware(MagicMock())
    span = MagicMock()
    span.is_recording.return_value = True

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-sem-auth", None)
    req = Request(scope, receive)

    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-sem-auth"
    keys = [c.args[0] for c in span.set_attribute.call_args_list]
    assert keys == ["qualidiagiq.trace_id_http"]


@pytest.mark.asyncio
async def test_otel_bearer_token_sem_payload_intermediario_nao_seta_tenant() -> None:
    """JWT com menos de 2 segmentos → não decodifica payload de ``tenant_id``."""
    mw = TraceContextMiddleware(MagicMock())
    span = MagicMock()
    span.is_recording.return_value = True

    async def call_next(_: Request) -> Response:
        return Response(b"ok")

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    scope = _scope_com_auth("trace-jwt-curto", "Bearer so_um_segmento")
    req = Request(scope, receive)

    with (
        patch(
            "src.presentation.api.middleware.trace_context.get_settings",
            return_value=MagicMock(otel_tracing_enabled=True),
        ),
        patch("opentelemetry.trace.get_current_span", return_value=span),
    ):
        resp = await mw.dispatch(req, call_next)

    assert resp.headers["X-Trace-Id"] == "trace-jwt-curto"
    keys = [c.args[0] for c in span.set_attribute.call_args_list]
    assert keys == ["qualidiagiq.trace_id_http"]
