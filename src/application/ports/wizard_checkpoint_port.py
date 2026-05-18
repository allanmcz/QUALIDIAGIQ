"""
Port — persistência de checkpoint LangGraph do wizard (memória episódica).

Camada: Application (Onda IA 1.1 — Fase H).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class WizardCheckpointPort(ABC):
    """Grava e recupera estado do wizard por ``thread_id`` (multi-tenant)."""

    @abstractmethod
    async def salvar(
        self,
        thread_id: UUID,
        tenant_id: UUID,
        checkpoint: dict[str, Any],
    ) -> None:
        """Upsert do checkpoint serializado (JSON compatível LangGraph)."""
        ...

    @abstractmethod
    async def carregar(
        self,
        thread_id: UUID,
        tenant_id: UUID,
    ) -> dict[str, Any] | None:
        """Retorna checkpoint ou ``None`` se inexistente."""
        ...

    @abstractmethod
    async def remover(self, thread_id: UUID, tenant_id: UUID) -> bool:
        """Remove checkpoint; ``True`` se havia registo."""
        ...
