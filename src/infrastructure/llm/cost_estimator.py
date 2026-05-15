"""
Estimador de custo LLM — stub (Fase 1 ADR-022).

Camada: Infrastructure
"""

from __future__ import annotations


class CostEstimator:
    """Reserva interface para Fase 2+; MVP devolve zero."""

    def estimate_usd(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> float:
        """Custo estimado em USD — sem tabela de preços nesta fase."""
        _ = (input_tokens, output_tokens, model)
        return 0.0
