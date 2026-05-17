"""
Port do Kanban operacional sobre ``diagnostico_plano_acao``.

Camada: Application (interface — Dependency Inversion Principle)
Implementação: ``src/infrastructure/adapters/postgres_plano_acao_kanban_adapter.py``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.domain.value_objects.status_execucao_plano_acao import StatusExecucaoPlanoAcao

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID


@dataclass(frozen=True)
class PlanoAcaoKanbanCard:
    """Card agregado: ação materializada + estado operacional + contadores."""

    plano_acao_id: UUID
    diagnostico_id: UUID
    tenant_id: UUID
    frente_indice: int
    frente_nome: str
    acao_indice: int
    texto_acao: str
    responsavel_sugerido: str | None
    prioridade_motor: int
    criticidade: str | None
    base_legal: str | None
    fase_pdca: str | None
    horizonte_planejado: str | None
    chave_quadro_legado: str
    status_execucao: StatusExecucaoPlanoAcao
    responsavel_operacional: str | None
    prazo_operacional: date | None
    bloqueio_motivo: str | None
    descricao_operacional: str | None
    ordem_kanban: int
    arquivado: bool
    comentarios_total: int
    subtarefas_total: int


@dataclass(frozen=True)
class PlanoAcaoKanbanBoard:
    """Board completo de um diagnóstico."""

    diagnostico_id: UUID
    tenant_id: UUID
    cards: tuple[PlanoAcaoKanbanCard, ...]


@dataclass(frozen=True)
class PlanoAcaoComentarioRegistro:
    """Comentário WORM persistido."""

    id: UUID
    plano_acao_id: UUID
    diagnostico_id: UUID
    tenant_id: UUID
    autor_label: str
    autor_email: str | None
    autor_user_id: UUID | None
    comentario: str
    sha256_payload: str
    criado_em: datetime


@dataclass(frozen=True)
class AtualizarEstadoKanbanInput:
    """Campos mutáveis do estado operacional (PATCH parcial)."""

    status_execucao: StatusExecucaoPlanoAcao | None = None
    responsavel_operacional: str | None = None
    prazo_operacional: date | None = None
    bloqueio_motivo: str | None = None
    descricao_operacional: str | None = None
    ordem_kanban: int | None = None
    limpar_prazo: bool = False
    limpar_bloqueio: bool = False


class PlanoAcaoKanbanPort(ABC):
    """Persistência do Kanban operacional do plano."""

    @abstractmethod
    async def listar_board(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        incluir_arquivados: bool = False,
    ) -> PlanoAcaoKanbanBoard:
        """Lista cards com estado; exclui arquivados por padrão."""

    @abstractmethod
    async def plano_acao_pertence_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
    ) -> bool:
        """Valida vínculo antes de mutações."""

    @abstractmethod
    async def atualizar_estado(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        dados: AtualizarEstadoKanbanInput,
    ) -> PlanoAcaoKanbanCard:
        """Upsert em ``diagnostico_plano_acao_estado``."""

    @abstractmethod
    async def definir_arquivado(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        arquivado: bool,
    ) -> PlanoAcaoKanbanCard:
        """Arquiva ou restaura card na visão padrão."""

    @abstractmethod
    async def inserir_comentario(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        autor_label: str,
        autor_email: str | None,
        autor_user_id: UUID | None,
        comentario: str,
        sha256_payload: str,
        criado_em: datetime,
    ) -> PlanoAcaoComentarioRegistro:
        """Insert append-only em ``diagnostico_plano_acao_comentario``."""

    @abstractmethod
    async def listar_comentarios(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        limite: int = 50,
    ) -> tuple[PlanoAcaoComentarioRegistro, ...]:
        """Lista comentários do card (mais recentes primeiro)."""

    @abstractmethod
    async def buscar_card(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
    ) -> PlanoAcaoKanbanCard | None:
        """Card único para resposta de mutação."""
