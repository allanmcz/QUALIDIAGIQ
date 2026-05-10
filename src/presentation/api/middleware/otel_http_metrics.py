"""
Middleware HTTP — contador de pedidos para métricas OpenTelemetry (S-02).

Camada: Presentation
"""

from __future__ import annotations

from opentelemetry.metrics import Meter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


class OtelHttpMetricsMiddleware(BaseHTTPMiddleware):
    """Incrementa `http.server.requests` por método, rota canónica e código HTTP."""

    def __init__(self, app: ASGIApp, *, meter: Meter) -> None:
        super().__init__(app)
        self._requests = meter.create_counter(
            "http.server.requests",
            unit="1",
            description="Total de pedidos HTTP processados pela API QualiDiagIQ",
        )

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        route = request.scope.get("route")
        path_tpl = getattr(route, "path", request.url.path) if route else request.url.path
        self._requests.add(
            1,
            {
                "http.method": request.method,
                "http.status_code": str(response.status_code),
                "http.route": path_tpl,
            },
        )
        return response
