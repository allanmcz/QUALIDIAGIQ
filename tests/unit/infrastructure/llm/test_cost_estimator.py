"""Testes do ``CostEstimator`` (stub Fase 1 ADR-022)."""

from __future__ import annotations

from src.infrastructure.llm.cost_estimator import CostEstimator


class TestCostEstimator:
    """MVP devolve zero até tabela de preços."""

    def test_estimate_usd_zero(self) -> None:
        est = CostEstimator()
        assert est.estimate_usd(input_tokens=1000, output_tokens=500, model="qualquer") == 0.0
