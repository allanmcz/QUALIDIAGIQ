"""Testes do repositório embutido de pesos macro (fallback sem Postgres)."""

from __future__ import annotations

from datetime import date

from src.domain.value_objects.score import (
    ROTULO_VERSAO_MACRO_EMBUTIDO,
    VIGENCIA_INICIO_PADRAO_PESO_MACRO,
    Dimensao,
)
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)


class TestEmbutidasNormativaScoreMacroRepository:
    """Vigência sintética estável — alinhada ao baseline da migração 0015."""

    def test_metadados_incluem_vigencia_e_rotulo(self) -> None:
        repo = EmbutidasNormativaScoreMacroRepository()
        meta = repo.obter_metadados_macro_validos_na_data(date(2030, 1, 1))
        assert len(meta) == 7
        m = meta[Dimensao.FISCAL]
        assert m.peso == 1.5
        assert m.vigencia_inicio == VIGENCIA_INICIO_PADRAO_PESO_MACRO
        assert m.vigencia_fim is None
        assert m.rotulo_versao == ROTULO_VERSAO_MACRO_EMBUTIDO
