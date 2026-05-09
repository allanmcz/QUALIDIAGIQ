"""
Port — consulta CNPJ em fontes públicas (BrasilAPI + fallback Minha Receita).

Camada: Application (contrato — Dependency Inversion)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CnpjProvedorExternoPort(ABC):
    """Busca cadastro CNPJ na rede; implementação HTTP na infrastructure."""

    @abstractmethod
    async def buscar_cnpj(self, cnpj_14: str) -> tuple[dict[str, Any], str, int, int]:
        """
        Retorna payload JSON bruto da fonte que respondeu.

        Returns:
            Tupla ``(payload, fonte, http_status, latencia_ms)`` onde ``fonte`` é
            ``brasil_api`` ou ``minha_receita``.

        Raises:
            ValueError: CNPJ inexistente (404 BrasilAPI) ou payload inválido.
            RuntimeError: falha em ambas as fontes.
        """
        ...
