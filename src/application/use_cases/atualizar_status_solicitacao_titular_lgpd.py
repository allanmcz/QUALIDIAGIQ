"""
Caso de uso: atualizar status de solicitação LGPD do titular.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.ports.lgpd_titular_solicitacao_port import (
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
)

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoAtualizarStatusSolicitacaoTitularLgpd:
    """Entrada do PATCH de status operacional LGPD."""

    tenant_id: UUID
    solicitacao_id: UUID
    status: StatusSolicitacaoTitular
    observacao_interna: str | None
    actor_user_id: UUID | None = None


class AtualizarStatusSolicitacaoTitularLgpd:
    """Atualiza status e observação interna de uma solicitação existente no tenant."""

    def __init__(self, port: LgpdTitularSolicitacaoPort) -> None:
        self._port = port

    async def execute(
        self,
        comando: ComandoAtualizarStatusSolicitacaoTitularLgpd,
    ) -> SolicitacaoTitular | None:
        observacao = (comando.observacao_interna or "").strip() or None
        return await self._port.atualizar_status(
            tenant_id=comando.tenant_id,
            solicitacao_id=comando.solicitacao_id,
            status=comando.status,
            observacao_interna=observacao,
            actor_user_id=comando.actor_user_id,
        )
