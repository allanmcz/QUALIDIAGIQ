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
        response.headers["X-Trace-Id"] = tid
        return response
