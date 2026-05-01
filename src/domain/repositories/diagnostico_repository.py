"""
Port (interface) de persistência de Diagnóstico.

Camada: Domain (interface — Dependency Inversion Principle)

Implementação concreta vive em:
    src/infrastructure/repositories/supabase_diagnostico_repository.py

Princípio: domain define o contrato, infrastructure implementa.
Isso permite trocar Supabase → PostgreSQL puro → MongoDB sem tocar nas regras de negócio.

Analogia para o Allan:
    É como definir uma interface no Delphi (`type IDiagnosticoRepo = interface`)
    que múltiplas implementações concretas podem honrar (Oracle, FireDAC, ZeosLib...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.entities.diagnostico import Diagnostico


class DiagnosticoRepository(ABC):
    """Port de persistência da entidade Diagnóstico."""

    @abstractmethod
    async def salvar(self, diagnostico: Diagnostico) -> None:
        """
        Persiste o agregado completo (insert ou update conforme existência).

        Idempotente em relação a `diagnostico.id` (UUID).
        """
        ...

    @abstractmethod
    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        """
        Busca diagnóstico por ID, **respeitando isolamento multi-tenant** (RLS).

        Returns:
            Diagnóstico se encontrado; None caso contrário.
        """
        ...

    @abstractmethod
    async def listar_por_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Diagnostico]:
        """Lista diagnósticos de um tenant, paginado."""
        ...

    @abstractmethod
    async def atualizar_relatorio_pdf_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        relatorio_pdf_url: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        """
        Atualiza apenas a URL do PDF com lock otimista (`versao_otimista`).

        Retorna:
            Diagnóstico atualizado se uma linha foi afetada; None se a versão não coincidir.
        """
        ...
