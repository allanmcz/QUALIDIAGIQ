"""Testes — métricas OTEL de domínio (no-op seguro sem provider)."""

from __future__ import annotations

from src.infrastructure.observability import qdi_otel_metrics


class TestQdiOtelMetrics:
    """Garante que ``record_*`` não levanta (SDK no-op em testes)."""

    def test_record_pdf_generation(self) -> None:
        for o in ("success", "timeout", "mock_fallback", "error"):
            qdi_otel_metrics.record_pdf_generation(outcome=o)

    def test_record_cnpj_lookup(self) -> None:
        qdi_otel_metrics.record_cnpj_lookup(fonte="brasil_api", http_status_group="2xx")
        qdi_otel_metrics.record_cnpj_lookup(fonte="minha_receita", http_status_group="timeout")
        qdi_otel_metrics.record_cnpj_lookup(fonte="error", http_status_group="unknown")

    def test_record_llm_recommendation(self) -> None:
        qdi_otel_metrics.record_llm_recommendation(adapter="ollama_rest", outcome="success")
        qdi_otel_metrics.record_llm_recommendation(
            adapter="langgraph_ollama", outcome="unexpected_error"
        )
        qdi_otel_metrics.record_llm_recommendation(adapter="anthropic", outcome="http_error")
        qdi_otel_metrics.record_llm_recommendation(adapter="openai_chat", outcome="success")
