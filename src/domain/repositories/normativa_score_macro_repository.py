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

    from src.domain.value_objects.score import Dimensao


class NormativaScoreMacroRepository(ABC):
    """Resolve pesos macro válidos na data de referência informada."""

    @abstractmethod
    def obter_pesos_macro_validos_na_data(self, data_referencia: date) -> dict[Dimensao, float]:
        """
        Retorna mapa completo dimensão → peso (> 0) vigente em `data_referencia`.

        Args:
            data_referencia: Data-canônica para resolver sobreposição de vigências.

        Returns:
            Um valor por cada membro de `Dimensao`.

        Raises:
            ValueError: vigência incompleta ou dados inválidos no backend configurado.
            RuntimeError: falha de infraestrutura (ex.: conexão PostgreSQL).
        """
        ...
