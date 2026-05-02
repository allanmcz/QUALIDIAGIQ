"""Testes do invariante de pesos macro completos (camada DOMAIN)."""

from __future__ import annotations

import pytest

from src.domain.value_objects.score import Dimensao, exigir_mapa_pesos_macro_completo


class TestExigirMapaPesosMacroCompleto:
    def test_aceita_mapa_com_sete_dimensoes_positivas(self) -> None:
        m = dict.fromkeys(Dimensao, 1.0)
        m[Dimensao.FISCAL] = 1.5
        exigir_mapa_pesos_macro_completo(m)

    def test_rejeita_dimensao_ausente(self) -> None:
        m = {Dimensao.FISCAL: 1.5}
        with pytest.raises(ValueError, match=r"falta a dimensão"):
            exigir_mapa_pesos_macro_completo(m)

    def test_rejeita_peso_nao_positivo(self) -> None:
        m = dict.fromkeys(Dimensao, 1.0)
        m[Dimensao.CONTABIL] = 0.0
        with pytest.raises(ValueError, match=r"deve ser > 0"):
            exigir_mapa_pesos_macro_completo(m)
