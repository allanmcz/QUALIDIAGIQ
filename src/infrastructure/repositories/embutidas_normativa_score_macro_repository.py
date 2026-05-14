"""
Adapter embutido — pesos macro iguais às constantes do domain (fallback sem Postgres).

Camada: Infrastructure
Implementa: NormativaScoreMacroRepository

Vigência: baseline fixa alinhada ao seed da migração 0015 (transparência quando não há DB).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import (
    PESOS_MACRO_DIMENSAO_SCORE_GERAL,
    ROTULO_VERSAO_MACRO_EMBUTIDO,
    VIGENCIA_INICIO_PADRAO_PESO_MACRO,
    Dimensao,
    PesoMacroNormativoVigente,
)

if TYPE_CHECKING:
    from datetime import date


class EmbutidasNormativaScoreMacroRepository(NormativaScoreMacroRepository):
    """Mesmos pesos de `PESOS_MACRO_DIMENSAO_SCORE_GERAL`; vigência sintética estável."""

    def obter_metadados_macro_validos_na_data(
        self, data_referencia: date
    ) -> dict[Dimensao, PesoMacroNormativoVigente]:
        _ = data_referencia
        return {
            dim: PesoMacroNormativoVigente(
                peso=float(w),
                vigencia_inicio=VIGENCIA_INICIO_PADRAO_PESO_MACRO,
                vigencia_fim=None,
                rotulo_versao=ROTULO_VERSAO_MACRO_EMBUTIDO,
            )
            for dim, w in PESOS_MACRO_DIMENSAO_SCORE_GERAL.items()
        }
