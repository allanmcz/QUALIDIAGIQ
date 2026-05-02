"""
Adapter embutido — pesos macro iguais às constantes do domain (fallback sem Postgres).

Camada: Infrastructure
Implementa: NormativaScoreMacroRepository
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import (
    PESOS_MACRO_DIMENSAO_SCORE_GERAL,
    Dimensao,
)

if TYPE_CHECKING:
    from datetime import date


class EmbutidasNormativaScoreMacroRepository(NormativaScoreMacroRepository):
    """Mesmos pesos de `PESOS_MACRO_DIMENSAO_SCORE_GERAL`; ignora calendário (baseline estável)."""

    def obter_pesos_macro_validos_na_data(self, data_referencia: date) -> dict[Dimensao, float]:
        _ = data_referencia
        return dict(PESOS_MACRO_DIMENSAO_SCORE_GERAL)
