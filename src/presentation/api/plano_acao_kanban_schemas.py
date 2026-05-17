"""
Schemas Pydantic v2 — Kanban operacional do plano de ação.

Camada: Presentation
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.value_objects.status_execucao_plano_acao import StatusExecucaoPlanoAcao

StatusExecucaoLiteral = Literal["pendente", "em_andamento", "bloqueado", "concluida"]


class PlanoAcaoKanbanCardSchema(BaseModel):
    """Card compacto do board."""

    plano_acao_id: UUID
    diagnostico_id: UUID
    frente_indice: int
    frente_nome: str
    acao_indice: int
    texto_acao: str
    responsavel_sugerido: str | None = None
    prioridade_motor: int
    criticidade: str | None = None
    base_legal: str | None = None
    fase_pdca: str | None = None
    horizonte_planejado: str | None = None
    chave_quadro_legado: str
    status_execucao: StatusExecucaoLiteral
    responsavel_operacional: str | None = None
    prazo_operacional: date | None = None
    bloqueio_motivo: str | None = None
    descricao_operacional: str | None = None
    ordem_kanban: int
    arquivado: bool
    comentarios_total: int
    subtarefas_total: int

    model_config = ConfigDict(from_attributes=True)


class PlanoAcaoKanbanBoardSchema(BaseModel):
    """Board agrupado por diagnóstico."""

    diagnostico_id: UUID
    cards: list[PlanoAcaoKanbanCardSchema] = Field(default_factory=list)


class PatchEstadoOperacionalPlanoAcaoRequest(BaseModel):
    """PATCH parcial do estado operacional."""

    status_execucao: StatusExecucaoLiteral | None = None
    responsavel_operacional: str | None = Field(default=None, max_length=500)
    prazo_operacional: date | None = None
    limpar_prazo: bool = False
    bloqueio_motivo: str | None = Field(default=None, max_length=2000)
    limpar_bloqueio: bool = False
    descricao_operacional: str | None = Field(default=None, max_length=4000)
    ordem_kanban: int | None = Field(default=None, ge=0)

    model_config = ConfigDict(extra="forbid")

    @field_validator("status_execucao")
    @classmethod
    def validar_status(cls, v: str | None) -> str | None:
        if v is not None and v not in StatusExecucaoPlanoAcao.valores_validos():
            raise ValueError(f"status_execucao inválido: {v}")
        return v


class PostComentarioPlanoAcaoRequest(BaseModel):
    """Corpo do POST de comentário WORM."""

    comentario: str = Field(min_length=1, max_length=8000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class PlanoAcaoComentarioSchema(BaseModel):
    """Comentário persistido."""

    id: UUID
    plano_acao_id: UUID
    autor_label: str
    autor_email: str | None = None
    comentario: str
    sha256_payload: str
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanoAcaoComentarioListaSchema(BaseModel):
    """Lista de comentários do card."""

    itens: list[PlanoAcaoComentarioSchema] = Field(default_factory=list)


class PatchArquivarPlanoAcaoRequest(BaseModel):
    """Arquivar ou restaurar card."""

    arquivado: bool

    model_config = ConfigDict(extra="forbid")
