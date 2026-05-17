"""
Casos de uso do Kanban operacional do plano de ação (Onda 1.0 V99).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.application.errors import DiagnosticoNaoEncontradoError
from src.application.ports.plano_acao_kanban_port import (
    AtualizarEstadoKanbanInput,
    PlanoAcaoComentarioRegistro,
    PlanoAcaoKanbanBoard,
    PlanoAcaoKanbanCard,
    PlanoAcaoKanbanPort,
)
from src.application.services.plano_acao_comentario_hash import (
    calcular_sha256_payload_comentario,
    montar_payload_hash_comentario,
)
from src.domain.value_objects.status_execucao_plano_acao import StatusExecucaoPlanoAcao

if TYPE_CHECKING:
    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository

logger = structlog.get_logger(__name__)


class PlanoAcaoKanbanNaoEncontradoError(ValueError):
    """Card ou plano inexistente para o diagnóstico/tenant."""


@dataclass(frozen=True)
class ComandoListarKanbanPlanoAcao:
    tenant_id: UUID
    diagnostico_id: UUID
    incluir_arquivados: bool = False


class ListarKanbanPlanoAcao:
    """GET board — exige diagnóstico existente no tenant."""

    def __init__(
        self,
        kanban: PlanoAcaoKanbanPort,
        diagnostico_repo: DiagnosticoRepository,
    ) -> None:
        self._kanban = kanban
        self._diagnostico_repo = diagnostico_repo

    async def execute(self, comando: ComandoListarKanbanPlanoAcao) -> PlanoAcaoKanbanBoard:
        d = await self._diagnostico_repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if d is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))
        return await self._kanban.listar_board(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            incluir_arquivados=comando.incluir_arquivados,
        )


@dataclass(frozen=True)
class ComandoAtualizarEstadoOperacionalPlanoAcao:
    tenant_id: UUID
    diagnostico_id: UUID
    plano_acao_id: UUID
    dados: AtualizarEstadoKanbanInput


class AtualizarEstadoOperacionalPlanoAcao:
    """PATCH estado operacional do card."""

    def __init__(
        self,
        kanban: PlanoAcaoKanbanPort,
        diagnostico_repo: DiagnosticoRepository,
    ) -> None:
        self._kanban = kanban
        self._diagnostico_repo = diagnostico_repo

    async def execute(self, comando: ComandoAtualizarEstadoOperacionalPlanoAcao) -> PlanoAcaoKanbanCard:
        await self._assert_diagnostico_e_plano(comando.tenant_id, comando.diagnostico_id, comando.plano_acao_id)
        if (
            comando.dados.status_execucao == StatusExecucaoPlanoAcao.BLOQUEADO
            and not (comando.dados.bloqueio_motivo or "").strip()
            and not comando.dados.limpar_bloqueio
        ):
            raise ValueError("Informe bloqueio_motivo quando o status for bloqueado.")
        card = await self._kanban.atualizar_estado(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
            dados=comando.dados,
        )
        logger.info(
            "kanban_estado_atualizado",
            plano_acao_id=str(comando.plano_acao_id),
            status=card.status_execucao.value,
        )
        return card

    async def _assert_diagnostico_e_plano(
        self, tenant_id: UUID, diagnostico_id: UUID, plano_acao_id: UUID
    ) -> None:
        d = await self._diagnostico_repo.buscar_por_id(diagnostico_id, tenant_id)
        if d is None:
            raise DiagnosticoNaoEncontradoError(str(diagnostico_id))
        ok = await self._kanban.plano_acao_pertence_diagnostico(
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
        )
        if not ok:
            raise PlanoAcaoKanbanNaoEncontradoError(
                f"plano_acao_id {plano_acao_id} não pertence ao diagnóstico."
            )


@dataclass(frozen=True)
class ComandoAdicionarComentarioPlanoAcao:
    tenant_id: UUID
    diagnostico_id: UUID
    plano_acao_id: UUID
    autor_label: str
    autor_email: str | None
    autor_user_id: UUID | None
    comentario: str


class AdicionarComentarioPlanoAcao:
    """POST comentário WORM com hash canónico."""

    def __init__(
        self,
        kanban: PlanoAcaoKanbanPort,
        diagnostico_repo: DiagnosticoRepository,
    ) -> None:
        self._kanban = kanban
        self._diagnostico_repo = diagnostico_repo

    async def execute(self, comando: ComandoAdicionarComentarioPlanoAcao) -> PlanoAcaoComentarioRegistro:
        texto = (comando.comentario or "").strip()
        if not texto:
            raise ValueError("comentario não pode ser vazio.")
        if len(texto) > 8000:
            raise ValueError("comentario excede 8000 caracteres.")
        d = await self._diagnostico_repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if d is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))
        ok = await self._kanban.plano_acao_pertence_diagnostico(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
        )
        if not ok:
            raise PlanoAcaoKanbanNaoEncontradoError(
                f"plano_acao_id {comando.plano_acao_id} não pertence ao diagnóstico."
            )
        criado_em = datetime.now(UTC)
        payload = montar_payload_hash_comentario(
            plano_acao_id=comando.plano_acao_id,
            diagnostico_id=comando.diagnostico_id,
            tenant_id=comando.tenant_id,
            autor_label=comando.autor_label.strip(),
            autor_email=comando.autor_email,
            autor_user_id=comando.autor_user_id,
            comentario=texto,
            criado_em=criado_em,
        )
        sha = calcular_sha256_payload_comentario(payload)
        registro = await self._kanban.inserir_comentario(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
            autor_label=comando.autor_label.strip(),
            autor_email=comando.autor_email,
            autor_user_id=comando.autor_user_id,
            comentario=texto,
            sha256_payload=sha,
            criado_em=criado_em,
        )
        logger.info(
            "kanban_comentario_criado",
            plano_acao_id=str(comando.plano_acao_id),
            comentario_id=str(registro.id),
        )
        return registro


@dataclass(frozen=True)
class ComandoArquivarPlanoAcaoKanban:
    tenant_id: UUID
    diagnostico_id: UUID
    plano_acao_id: UUID
    arquivado: bool


class ArquivarPlanoAcaoKanban:
    """PATCH arquivar/desarquivar."""

    def __init__(
        self,
        kanban: PlanoAcaoKanbanPort,
        diagnostico_repo: DiagnosticoRepository,
    ) -> None:
        self._kanban = kanban
        self._diagnostico_repo = diagnostico_repo

    async def execute(self, comando: ComandoArquivarPlanoAcaoKanban) -> PlanoAcaoKanbanCard:
        d = await self._diagnostico_repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if d is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))
        ok = await self._kanban.plano_acao_pertence_diagnostico(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
        )
        if not ok:
            raise PlanoAcaoKanbanNaoEncontradoError(
                f"plano_acao_id {comando.plano_acao_id} não pertence ao diagnóstico."
            )
        return await self._kanban.definir_arquivado(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
            arquivado=comando.arquivado,
        )


@dataclass(frozen=True)
class ComandoListarComentariosPlanoAcao:
    tenant_id: UUID
    diagnostico_id: UUID
    plano_acao_id: UUID
    limite: int = 50


class ListarComentariosPlanoAcao:
    """GET comentários de um card."""

    def __init__(self, kanban: PlanoAcaoKanbanPort) -> None:
        self._kanban = kanban

    async def execute(
        self, comando: ComandoListarComentariosPlanoAcao
    ) -> tuple[PlanoAcaoComentarioRegistro, ...]:
        return await self._kanban.listar_comentarios(
            tenant_id=comando.tenant_id,
            diagnostico_id=comando.diagnostico_id,
            plano_acao_id=comando.plano_acao_id,
            limite=comando.limite,
        )
