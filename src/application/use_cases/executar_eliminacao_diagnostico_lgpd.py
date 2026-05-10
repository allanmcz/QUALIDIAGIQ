"""
Caso de uso — eliminação física de diagnóstico após deferimento LGPD (art. 18).

Camada: Application

Decisão produto J4 / DEV_09052026_V2: permitir DELETE apenas quando o diagnóstico não está
``finalizado`` (sem evidência WORM); caso contrário, orientar anonimização.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort
from src.application.ports.lgpd_titular_solicitacao_port import (
    LgpdTitularSolicitacaoPort,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoExecutarEliminacaoDiagnosticoLgpd:
    tenant_id: UUID
    actor_user_id: UUID
    diagnostico_id: UUID
    solicitacao_id: UUID


class ExecutarEliminacaoDiagnosticoLgpd:
    """Orquestra validação da solicitação ``eliminacao`` e transação física na base."""

    def __init__(
        self,
        *,
        port_solicitacoes: LgpdTitularSolicitacaoPort,
        executor: LgpdEliminacaoExecutorPort,
    ) -> None:
        self._port = port_solicitacoes
        self._executor = executor

    async def execute(self, cmd: ComandoExecutarEliminacaoDiagnosticoLgpd) -> None:
        sol = await self._port.buscar_por_id(
            tenant_id=cmd.tenant_id,
            solicitacao_id=cmd.solicitacao_id,
        )
        if sol is None:
            raise ValueError("Solicitação LGPD não encontrada.")
        if sol.tipo != TipoSolicitacaoTitular.ELIMINACAO:
            raise ValueError("A solicitação não é do tipo eliminação.")
        if sol.status != StatusSolicitacaoTitular.DEFERIDA:
            raise ValueError("A solicitação deve estar deferida antes da execução técnica.")
        if sol.diagnostico_id is None:
            raise ValueError("Solicitação sem diagnóstico vinculado.")
        if sol.diagnostico_id != cmd.diagnostico_id:
            raise ValueError("Diagnóstico informado diverge da solicitação.")

        await self._executor.aplicar_eliminacao_diagnostico(
            tenant_id=cmd.tenant_id,
            diagnostico_id=cmd.diagnostico_id,
            solicitacao_id=cmd.solicitacao_id,
            actor_user_id=cmd.actor_user_id,
        )
