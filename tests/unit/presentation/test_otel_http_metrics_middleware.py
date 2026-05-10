"""Testes do middleware de contagem HTTP para OpenTelemetry."""

from __future__ import annotations

from unittest.mock import MagicMock

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.presentation.api.middleware.otel_http_metrics import OtelHttpMetricsMiddleware


async def _home(_request: object) -> PlainTextResponse:
    return PlainTextResponse("ok", status_code=200)


def test_otel_http_metrics_incrementa_contador() -> None:
    """Cada pedido completo incrementa `http.server.requests` com etiquetas mínimas."""
    counter = MagicMock()
    meter = MagicMock()
    meter.create_counter.return_value = counter

    app = Starlette(routes=[Route("/", _home)])
    wrapped = OtelHttpMetricsMiddleware(app, meter=meter)

    client = TestClient(wrapped)
    res = client.get("/")
    assert res.status_code == 200
    meter.create_counter.assert_called_once()
    counter.add.assert_called_once()
    amount, attrs = counter.add.call_args[0]
    assert amount == 1
    assert attrs["http.method"] == "GET"
    assert attrs["http.status_code"] == "200"
