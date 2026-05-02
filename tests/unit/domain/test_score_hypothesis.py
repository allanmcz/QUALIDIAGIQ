"""Testes de propriedade (Hypothesis) para invariantes de ScoreNumerico — camada DOMAIN."""

from __future__ import annotations

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from src.domain.value_objects.score import ScoreNumerico


class TestScoreNumericoHypothesis:
    """Garante que valores em [0,100] e peso não negativo sempre constroem o VO."""

    @given(
        st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0.0, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    def test_aceita_valores_validos(self, valor: float, peso: float) -> None:
        sn = ScoreNumerico(valor=valor, peso_total_aplicado=peso)
        assert 0.0 <= sn.valor <= 100.0

    @given(st.floats(max_value=-1e-9, allow_nan=False, allow_infinity=False))
    def test_rejeita_estritamente_negativo(self, valor: float) -> None:
        assume(valor < 0)
        with pytest.raises(ValueError, match="entre 0 e 100"):
            ScoreNumerico(valor=valor, peso_total_aplicado=1.0)

    @given(st.floats(min_value=100.0 + 1e-9, max_value=1e6, allow_nan=False, allow_infinity=False))
    def test_rejeita_acima_de_cem(self, valor: float) -> None:
        with pytest.raises(ValueError, match="entre 0 e 100"):
            ScoreNumerico(valor=valor, peso_total_aplicado=1.0)

    def test_rejeita_peso_negativo(self) -> None:
        with pytest.raises(ValueError, match="Peso total"):
            ScoreNumerico(valor=50.0, peso_total_aplicado=-1.0)
