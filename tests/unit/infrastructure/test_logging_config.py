"""Testes da configuração de logging estruturado (structlog + OTEL)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.infrastructure.config.logging import _processor_otel_trace, configurar_logging


def test_processor_otel_trace_anexa_ids_quando_contexto_valido() -> None:
    fake_ctx = SimpleNamespace(is_valid=True, trace_id=0xABC, span_id=0xDEF)
    fake_span = SimpleNamespace(get_span_context=lambda: fake_ctx)
    fake_trace = SimpleNamespace(get_current_span=lambda: fake_span)

    with patch.dict("sys.modules", {"opentelemetry": SimpleNamespace(trace=fake_trace)}):
        out = _processor_otel_trace(MagicMock(), "info", {"event": "x"})

    assert out["trace_id"] == "00000000000000000000000000000abc"
    assert out["span_id"] == "0000000000000def"


def test_processor_otel_trace_sem_contexto_valido_nao_anexa_ids() -> None:
    fake_ctx = SimpleNamespace(is_valid=False, trace_id=1, span_id=2)
    fake_span = SimpleNamespace(get_span_context=lambda: fake_ctx)
    fake_trace = SimpleNamespace(get_current_span=lambda: fake_span)

    with patch.dict("sys.modules", {"opentelemetry": SimpleNamespace(trace=fake_trace)}):
        out = _processor_otel_trace(MagicMock(), "info", {"event": "x"})

    assert "trace_id" not in out
    assert "span_id" not in out


def test_processor_otel_trace_falha_import_retorna_evento_original() -> None:
    with patch.dict("sys.modules", {"opentelemetry": None}):
        out = _processor_otel_trace(MagicMock(), "info", {"event": "x"})
    assert out == {"event": "x"}


def test_configurar_logging_production_usa_json_renderer() -> None:
    with patch("src.infrastructure.config.logging.structlog.configure") as mock_cfg:
        configurar_logging("production")

    processors = mock_cfg.call_args.kwargs["processors"]
    assert any(type(p).__name__ == "JSONRenderer" for p in processors)


def test_configurar_logging_dev_usa_console_renderer() -> None:
    with patch("src.infrastructure.config.logging.structlog.configure") as mock_cfg:
        configurar_logging("development")

    processors = mock_cfg.call_args.kwargs["processors"]
    assert any(type(p).__name__ == "ConsoleRenderer" for p in processors)
