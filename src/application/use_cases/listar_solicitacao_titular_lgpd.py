"""
Caso de uso: listar solicitações LGPD do titular por tenant.

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
class ComandoListarSolicitacaoTitularLgpd:
    """Entrada para listagem paginada simples."""

    tenant_id: UUID
    status: StatusSolicitacaoTitular | None = None
    limit: int = 50


class ListarSolicitacaoTitularLgpd:
    """Lista solicitações em ordem decrescente de criação."""

    def __init__(self, port: LgpdTitularSolicitacaoPort) -> None:
        self._port = port

    async def execute(
        self,
        comando: ComandoListarSolicitacaoTitularLgpd,
    ) -> list[SolicitacaoTitular]:
        limit = max(1, min(comando.limit, 200))
        return await self._port.listar_por_tenant(
            tenant_id=comando.tenant_id,
            status=comando.status,
            limit=limit,
        )
