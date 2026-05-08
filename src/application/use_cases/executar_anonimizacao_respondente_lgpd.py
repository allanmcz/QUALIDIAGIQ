"""
Caso de uso — executar anonimização de PII do respondente após deferimento LGPD.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.ports.lgpd_anonimizacao_executor_port import (
    LgpdAnonimizacaoExecutorPort,
)
from src.application.ports.lgpd_titular_solicitacao_port import (
    LgpdTitularSolicitacaoPort,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoExecutarAnonimizacaoRespondenteLgpd:
    tenant_id: UUID
    actor_user_id: UUID
    diagnostico_id: UUID
    solicitacao_id: UUID


class ExecutarAnonimizacaoRespondenteLgpd:
    """Orquestra validação da solicitação e transação física na base."""

    def __init__(
        self,
        *,
        port_solicitacoes: LgpdTitularSolicitacaoPort,
        executor: LgpdAnonimizacaoExecutorPort,
    ) -> None:
        self._port = port_solicitacoes
        self._executor = executor

    async def execute(self, cmd: ComandoExecutarAnonimizacaoRespondenteLgpd) -> None:
        sol = await self._port.buscar_por_id(
            tenant_id=cmd.tenant_id,
            solicitacao_id=cmd.solicitacao_id,
        )
        if sol is None:
            raise ValueError("Solicitação LGPD não encontrada.")
        if sol.tipo != TipoSolicitacaoTitular.ANONIMIZACAO:
            raise ValueError("A solicitação não é do tipo anonimização.")
        if sol.status != StatusSolicitacaoTitular.DEFERIDA:
            raise ValueError("A solicitação deve estar deferida antes da execução técnica.")
        if sol.diagnostico_id is None:
            raise ValueError("Solicitação sem diagnóstico vinculado.")
        if sol.diagnostico_id != cmd.diagnostico_id:
            raise ValueError("Diagnóstico informado diverge da solicitação.")

        await self._executor.aplicar_anonimizacao_respondente(
            tenant_id=cmd.tenant_id,
            diagnostico_id=cmd.diagnostico_id,
            solicitacao_id=cmd.solicitacao_id,
            actor_user_id=cmd.actor_user_id,
        )
