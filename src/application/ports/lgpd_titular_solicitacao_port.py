"""
Port de solicitações LGPD do titular (art. 18) por tenant.

Camada: Application (interface — Dependency Inversion Principle)
Implementação concreta: ``src/infrastructure/adapters/postgres_lgpd_titular_solicitacao_adapter.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class TipoSolicitacaoTitular(StrEnum):
    """Tipos operacionais aceitos para o fluxo de privacidade."""

    ACESSO = "acesso"
    CORRECAO = "correcao"
    ANONIMIZACAO = "anonimizacao"
    ELIMINACAO = "eliminacao"
    PORTABILIDADE = "portabilidade"
    OPOSICAO = "oposicao"


class StatusSolicitacaoTitular(StrEnum):
    """Status de acompanhamento da solicitação no backoffice."""

    RECEBIDA = "recebida"
    EM_ANALISE = "em_analise"
    DEFERIDA = "deferida"
    INDEFERIDA = "indeferida"
    CONCLUIDA = "concluida"


class CanalSolicitacaoTitular(StrEnum):
    """Canal de entrada do pedido do titular."""

    PLATAFORMA = "plataforma"
    SELF_SERVICE = "self_service"
    DPO_EMAIL = "dpo_email"


@dataclass(frozen=True)
class SolicitacaoTitular:
    """Snapshot de uma solicitação LGPD persistida."""

    id: UUID
    tenant_id: UUID
    diagnostico_id: UUID | None
    tipo: TipoSolicitacaoTitular
    status: StatusSolicitacaoTitular
    canal: CanalSolicitacaoTitular
    solicitante_email: str
    payload: dict[str, Any]
    observacao_interna: str | None
    actor_user_id: UUID | None
    criado_em: datetime
    atualizado_em: datetime


class LgpdTitularSolicitacaoPort(ABC):
    """Contrato para registrar, listar e atualizar solicitações do titular."""

    @abstractmethod
    async def criar(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID | None,
        tipo: TipoSolicitacaoTitular,
        canal: CanalSolicitacaoTitular,
        solicitante_email: str,
        payload: dict[str, Any],
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular:
        """Insere uma nova solicitação com status inicial ``recebida``."""

    @abstractmethod
    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        status: StatusSolicitacaoTitular | None,
        limit: int,
    ) -> list[SolicitacaoTitular]:
        """Lista solicitações do tenant, mais recentes primeiro."""

    @abstractmethod
    async def buscar_por_id(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
    ) -> SolicitacaoTitular | None:
        """Retorna a solicitação do tenant ou ``None``."""

    @abstractmethod
    async def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
        status: StatusSolicitacaoTitular,
        observacao_interna: str | None,
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular | None:
        """Atualiza status e observação. Retorna ``None`` quando o ID não pertence ao tenant."""
