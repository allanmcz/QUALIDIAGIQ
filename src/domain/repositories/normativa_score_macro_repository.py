"""
Port de consulta aos pesos macro por dimensão (agregação do score geral).

Camada: Domain (interface — Dependency Inversion Principle)

Implementações:
    src/infrastructure/repositories/embutidas_normativa_score_macro_repository.py
    src/infrastructure/repositories/postgres_normativa_score_macro_repository.py

Base normativa / produto:
    Transparência metodológica (M03); vigência alinhada ao princípio de versionamento
    normativo Tributiq (LC 214/2025 — previsibilidade ao contribuinte).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from src.domain.value_objects.score import Dimensao, PesoMacroNormativoVigente


class NormativaScoreMacroRepository(ABC):
    """Resolve pesos macro válidos na data de referência informada (com rasto de vigência)."""

    @abstractmethod
    def obter_metadados_macro_validos_na_data(
        self, data_referencia: date
    ) -> dict[Dimensao, PesoMacroNormativoVigente]:
        """
        Retorna mapa completo dimensão → metadado (peso + vigência) vigente em `data_referencia`.

        Args:
            data_referencia: Data-canônica para resolver sobreposição de vigências.

        Returns:
            Um valor por cada membro de `Dimensao`.

        Raises:
            ValueError: vigência incompleta, dimensão desconhecida no backend ou peso inválido.
            RuntimeError: falha de infraestrutura (ex.: conexão PostgreSQL).
        """
        ...

    def obter_pesos_macro_validos_na_data(self, data_referencia: date) -> dict[Dimensao, float]:
        """
        Mapa dimensão → peso (> 0) — atalho usado pelo motor de score.

        Implementação padrão deriva de ``obter_metadados_macro_validos_na_data`` e valida
        completude com ``exigir_mapa_pesos_macro_completo``.
        """
        from src.domain.value_objects.score import exigir_mapa_pesos_macro_completo

        meta = self.obter_metadados_macro_validos_na_data(data_referencia)
        pesos = {d: m.peso for d, m in meta.items()}
        exigir_mapa_pesos_macro_completo(pesos)
        return pesos
