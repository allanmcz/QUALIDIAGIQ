"""
Middleware HTTP — correlaciona requisições com `X-Trace-Id` (observabilidade MVP).

Camada: Presentation
Analogia: equivale a um GUID de sessão Oracle gravado em package context —
          aqui propagamos no header de resposta para suporte e logs futuros.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.config.settings import get_settings

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
        response = await call_next(request)
        settings = get_settings()
        if settings.otel_tracing_enabled:
            try:
                from opentelemetry import trace

                span = trace.get_current_span()
                if span.is_recording():
                    span.set_attribute("qualidiagiq.trace_id_http", tid)
            except Exception:
                pass
        response.headers["X-Trace-Id"] = tid
        return response
