"""
Métricas de domínio OpenTelemetry (QDI - Onda 3.5 / MANUS R-004 a R-008).

Contadores de melhor esforço: sem ``MeterProvider`` configurado, o SDK usa no-op
(instrumentação neutra em testes e em dev sem OTLP).

Camada: Infrastructure (sem dependência de FastAPI).
"""

from __future__ import annotations

from typing import Literal

from opentelemetry import metrics

_meter = metrics.get_meter(__name__, version="0.0.0")

_pdf_generation = _meter.create_counter(
    "qdi.pdf.generation.total",
    unit="1",
    description="Resultado da geração de PDF do relatório (WeasyPrint)",
)

_cnpj_lookup = _meter.create_counter(
    "qdi.cnpj.lookup.total",
    unit="1",
    description="Consultas CNPJ (fonte e resultado agregados)",
)

_llm_recommendation = _meter.create_counter(
    "qdi.llm.recommendation.total",
    unit="1",
    description="Chamadas ao serviço de recomendação LLM",
)


def record_pdf_generation(
    *,
    outcome: Literal["success", "timeout", "mock_fallback", "error"],
) -> None:
    """Regista desfecho da geração de PDF (não inclui PII)."""
    _pdf_generation.add(1, {"qdi.outcome": outcome})


def record_cnpj_lookup(
    *,
    fonte: Literal["brasil_api", "minha_receita", "cache", "error"],
    http_status_group: Literal["2xx", "4xx", "5xx", "timeout", "rede", "unknown"] = "unknown",
) -> None:
    """Regista consulta CNPJ (radical não é métrica — só fonte e classe HTTP)."""
    _cnpj_lookup.add(1, {"qdi.fonte": fonte, "qdi.http_status_group": http_status_group})


def record_llm_recommendation(
    *,
    adapter: Literal["ollama_rest", "langgraph_ollama", "anthropic", "openai_chat"],
    outcome: Literal["success", "http_error", "unexpected_error"],
) -> None:
    """Regista chamada ao LLM de recomendação."""
    _llm_recommendation.add(1, {"qdi.adapter": adapter, "qdi.outcome": outcome})
