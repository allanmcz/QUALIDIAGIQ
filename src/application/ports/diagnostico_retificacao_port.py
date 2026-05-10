"""
Port de persistência de retificações de diagnóstico (append-only).

Camada: Application (interface)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class DiagnosticoRetificacaoRegisto:
    """Linha materializada de uma retificação."""

    id: UUID
    tenant_id: UUID
    diagnostico_original_id: UUID
    hash_diagnostico_original_sha256: str
    motivo_retificacao: str
    payload_retificacao: dict[str, Any]
    hash_retificacao_sha256: str
    actor_user_id: UUID | None
    criado_em: datetime


class DiagnosticoRetificacaoPort(ABC):
    """Contrato insert/list para trilha de retificações."""

    @abstractmethod
    async def inserir(
        self,
        *,
        retificacao_id: UUID,
        tenant_id: UUID,
        diagnostico_original_id: UUID,
        hash_diagnostico_original_sha256: str,
        motivo_retificacao: str,
        payload_retificacao: dict[str, Any],
        hash_retificacao_sha256: str,
        actor_user_id: UUID | None,
    ) -> DiagnosticoRetificacaoRegisto:
        """INSERT único (append-only)."""

    @abstractmethod
    async def listar_por_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_original_id: UUID,
        limit: int,
    ) -> list[DiagnosticoRetificacaoRegisto]:
        """Lista mais recentes primeiro."""
