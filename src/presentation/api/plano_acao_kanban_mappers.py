"""Mapeamento domain → schemas HTTP do Kanban do plano."""

from __future__ import annotations

from src.application.ports.plano_acao_kanban_port import (
    PlanoAcaoComentarioRegistro,
    PlanoAcaoKanbanBoard,
    PlanoAcaoKanbanCard,
)
from src.presentation.api.plano_acao_kanban_schemas import (
    PlanoAcaoComentarioSchema,
    PlanoAcaoKanbanBoardSchema,
    PlanoAcaoKanbanCardSchema,
)


def card_para_schema(card: PlanoAcaoKanbanCard) -> PlanoAcaoKanbanCardSchema:
    return PlanoAcaoKanbanCardSchema(
        plano_acao_id=card.plano_acao_id,
        diagnostico_id=card.diagnostico_id,
        frente_indice=card.frente_indice,
        frente_nome=card.frente_nome,
        acao_indice=card.acao_indice,
        texto_acao=card.texto_acao,
        responsavel_sugerido=card.responsavel_sugerido,
        prioridade_motor=card.prioridade_motor,
        criticidade=card.criticidade,
        base_legal=card.base_legal,
        fase_pdca=card.fase_pdca,
        horizonte_planejado=card.horizonte_planejado,
        chave_quadro_legado=card.chave_quadro_legado,
        status_execucao=card.status_execucao.value,
        responsavel_operacional=card.responsavel_operacional,
        prazo_operacional=card.prazo_operacional,
        bloqueio_motivo=card.bloqueio_motivo,
        descricao_operacional=card.descricao_operacional,
        ordem_kanban=card.ordem_kanban,
        arquivado=card.arquivado,
        comentarios_total=card.comentarios_total,
        subtarefas_total=card.subtarefas_total,
    )


def board_para_schema(board: PlanoAcaoKanbanBoard) -> PlanoAcaoKanbanBoardSchema:
    return PlanoAcaoKanbanBoardSchema(
        diagnostico_id=board.diagnostico_id,
        cards=[card_para_schema(c) for c in board.cards],
    )


def comentario_para_schema(c: PlanoAcaoComentarioRegistro) -> PlanoAcaoComentarioSchema:
    return PlanoAcaoComentarioSchema(
        id=c.id,
        plano_acao_id=c.plano_acao_id,
        autor_label=c.autor_label,
        autor_email=c.autor_email,
        comentario=c.comentario,
        sha256_payload=c.sha256_payload,
        criado_em=c.criado_em,
    )
