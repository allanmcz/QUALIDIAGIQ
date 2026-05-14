"""
Middleware HTTP — correlaciona requisições com `X-Trace-Id` (observabilidade MVP).

Camada: Presentation
Analogia: equivale a um GUID de sessão Oracle gravado em package context —
          aqui propagamos no header de resposta para suporte e logs futuros.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, unbind_contextvars

from src.infrastructure.config.settings import get_settings

_std_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Gera ou repassa `X-Trace-Id` e disponibiliza em `request.state.trace_id`."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        raw = request.headers.get("x-trace-id") or request.headers.get("X-Trace-Id")
        tid = raw.strip() if raw and str(raw).strip() else str(uuid4())
        request.state.trace_id = tid
        # Correlação structlog (QDI — observabilidade): não confundir com trace_id OTEL (hex no processor).
        bind_contextvars(http_trace_id=tid)
        try:
            response = await call_next(request)
        finally:
            unbind_contextvars("http_trace_id")
        settings = get_settings()
        if settings.otel_tracing_enabled:
            try:
                from opentelemetry import trace

                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("qualidiagiq.trace_id_http", tid)
                    auth_raw = request.headers.get("authorization")
                    if auth_raw and str(auth_raw).strip().lower().startswith("bearer "):
                        token = str(auth_raw).strip()[7:].strip().split()[0]
                        parts = token.split(".")
                        if len(parts) >= 2:
                            pad = "=" * (-len(parts[1]) % 4)
                            payload_b = base64.urlsafe_b64decode(parts[1] + pad)
                            payload = json.loads(payload_b.decode("utf-8"))
                            claim_tid = payload.get("tenant_id")
                            if claim_tid:
                                span.set_attribute("tenant_id", str(claim_tid))
            except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
                _std_log.warning(
                    "otel_tenant_claim_decode_falhou",
                    extra={"erro": str(e)},
                )
            except Exception:
                pass
        response.headers["X-Trace-Id"] = tid
        return response
