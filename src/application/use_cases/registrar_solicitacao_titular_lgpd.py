"""
Caso de uso: registrar solicitação LGPD do titular (art. 18).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.infrastructure.email_verificacao.codigo_store import normalizar_email

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoRegistrarSolicitacaoTitularLgpd:
    """Entrada para criação de pedido de titular."""

    tenant_id: UUID
    diagnostico_id: UUID | None
    tipo: TipoSolicitacaoTitular
    canal: CanalSolicitacaoTitular
    solicitante_email: str
    payload: dict[str, Any]
    actor_user_id: UUID | None = None


class RegistrarSolicitacaoTitularLgpd:
    """Registra solicitação com normalização mínima de e-mail e payload."""

    def __init__(self, port: LgpdTitularSolicitacaoPort) -> None:
        self._port = port

    async def execute(
        self,
        comando: ComandoRegistrarSolicitacaoTitularLgpd,
    ) -> SolicitacaoTitular:
        email = normalizar_email(comando.solicitante_email)
        if len(email) < 5:
            raise ValueError("E-mail do solicitante inválido para fluxo LGPD.")
        payload = comando.payload if isinstance(comando.payload, dict) else {}
        return await self._port.criar(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            tipo=comando.tipo,
            canal=comando.canal,
            solicitante_email=email,
            payload=payload,
            actor_user_id=comando.actor_user_id,
        )
