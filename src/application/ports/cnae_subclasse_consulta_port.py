"""
Port — consulta somente leitura à tabela de subclass CNAE (schema qdi).

Camada: Application (interface — Dependency Inversion).

Analogia Delphi: interface que um DataModule poderia implementar com query parametrizada.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo


class CnaeSubclasseConsultaPort(ABC):
    """Contrato para busca textual/por prefixo numérico em CNAE 2.3."""

    @abstractmethod
    async def buscar(self, *, consulta: str, limite: int) -> list[CnaeSubclasseResumo]:
        """
        Retorna até `limite` subclasses vigentes (deleted_at nulo).

        Args:
            consulta: texto livre ou prefixo numérico (mínimo 2 caracteres tratados no use case).
            limite: máximo de linhas (1..50).

        Returns:
            Lista ordenada por subclasse_id ascendente.
        """
        ...
