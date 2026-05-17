"""
Port de arquivo operacional de empresa (CNPJ) no painel consultor.

Camada: Application
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class EmpresaPainelArquivoPort(ABC):
    """Marca CNPJ como arquivado no tenant — oculta da listagem sem apagar diagnósticos."""

    @abstractmethod
    async def definir_arquivado(
        self,
        tenant_id: UUID,
        empresa_cnpj: str,
        *,
        arquivado: bool,
        actor_user_id: UUID | None = None,
    ) -> bool:
        """
        Define estado de arquivo.

        Returns:
            True se o estado mudou; False se já estava no estado pedido.
        """
        ...

    @abstractmethod
    async def esta_arquivada(self, tenant_id: UUID, empresa_cnpj: str) -> bool:
        """Indica se o CNPJ está arquivado no tenant."""
        ...

    @abstractmethod
    async def listar_cnpjs_arquivados(self, tenant_id: UUID) -> frozenset[str]:
        """CNPJs arquivados do tenant (14 dígitos)."""
        ...
