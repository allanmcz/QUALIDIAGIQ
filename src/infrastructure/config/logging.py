"""
Configuração global structlog (JSON em produção, console em desenvolvimento).

Camada: Infrastructure
Handoff Sprint 11 — correlação opcional com trace_id/span_id OpenTelemetry quando span ativo.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, MutableMapping
from typing import Any, cast

import structlog

Proc = Callable[
    [Any, str, MutableMapping[str, Any]],
    MutableMapping[str, Any] | str | bytes | bytearray | tuple[Any, ...],
]


def _processor_otel_trace(
    logger: object, method_name: str, event_dict: dict[str, object]
) -> dict[str, object]:
    """Enriquece evento com trace_id/span_id do span atual (best-effort)."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:
        pass
    return event_dict


def configurar_logging(app_env: str) -> None:
    """
    Inicializa structlog uma vez por processo.

    Produção: JSON linha a linha (agregadores).
    Desenvolvimento: ConsoleRenderer colorido.
    """
    nivel = logging.INFO
    logging.basicConfig(level=nivel, format="%(message)s")

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _processor_otel_trace,
        timestamper,
    ]

    if (app_env or "").strip().lower() == "production":
        processors = [*shared, structlog.processors.JSONRenderer()]
    else:
        processors = [*shared, structlog.dev.ConsoleRenderer(colors=True)]

    structlog.configure(
        processors=cast("Iterable[Proc]", processors),
        wrapper_class=structlog.make_filtering_bound_logger(nivel),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
