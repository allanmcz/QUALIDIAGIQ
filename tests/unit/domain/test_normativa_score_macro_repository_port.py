"""Cobre o método concreto ``obter_pesos_macro_validos_na_data`` do port de domínio."""

from __future__ import annotations

from datetime import date

from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import (
    VIGENCIA_INICIO_PADRAO_PESO_MACRO,
    Dimensao,
    PesoMacroNormativoVigente,
)


class _RepoStub(NormativaScoreMacroRepository):
    """Implementa só metadados; o atalho de pesos deve percorrer linhas 55-60 do port."""

    def obter_metadados_macro_validos_na_data(
        self, data_referencia: date
    ) -> dict[Dimensao, PesoMacroNormativoVigente]:
        _ = data_referencia
        meta = PesoMacroNormativoVigente(
            peso=1.0,
            vigencia_inicio=VIGENCIA_INICIO_PADRAO_PESO_MACRO,
            vigencia_fim=None,
            rotulo_versao="unit:stub",
        )
        return dict.fromkeys(Dimensao, meta)


class TestNormativaScoreMacroRepositoryPort:
    def test_obter_pesos_macro_validos_na_data(self) -> None:
        repo = _RepoStub()
        pesos = repo.obter_pesos_macro_validos_na_data(date(2026, 5, 1))
        assert len(pesos) == len(Dimensao)
        assert all(p == 1.0 for p in pesos.values())
