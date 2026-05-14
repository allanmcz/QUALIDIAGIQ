"""
Adapter embutido — sem overlay de pesos por pergunta (sem Postgres).

Camada: Infrastructure
Implementa: NormativaPerguntaPesoRepository
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.domain.repositories.normativa_pergunta_peso_repository import (
    NormativaPerguntaPesoRepository,
)
from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente

if TYPE_CHECKING:
    from datetime import date


class EmbutidasNormativaPerguntaPesoRepository(NormativaPerguntaPesoRepository):
    """Sem linhas normativas em BD — o catálogo JSON é a única fonte."""

    def obter_metadados_por_codigo_validos_na_data(
        self,
        data_referencia: date,
        codigos: frozenset[str],
    ) -> dict[str, PesoPerguntaNormativoVigente]:
        _ = (data_referencia, codigos)
        return {}
