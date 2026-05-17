"""
Adapter Postgres para ``PlanoAcaoKanbanPort``.

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
import structlog
from psycopg2.extras import RealDictCursor

from src.application.ports.plano_acao_kanban_port import (
    AtualizarEstadoKanbanInput,
    PlanoAcaoComentarioRegistro,
    PlanoAcaoKanbanBoard,
    PlanoAcaoKanbanCard,
    PlanoAcaoKanbanPort,
)
from src.domain.value_objects.status_execucao_plano_acao import StatusExecucaoPlanoAcao

logger = structlog.get_logger(__name__)

_SELECT_CARD_BASE = """
SELECT
    pa.id AS plano_acao_id,
    pa.diagnostico_id,
    pa.tenant_id,
    pa.frente_indice,
    pa.frente_nome,
    pa.acao_indice,
    pa.texto_acao,
    pa.responsavel_sugerido,
    pa.prioridade_motor,
    pa.criticidade,
    pa.base_legal,
    pa.fase_pdca,
    pa.horizonte_planejado,
    pa.ordem_exibicao,
    COALESCE(e.status_execucao, 'pendente') AS status_execucao,
    e.responsavel_operacional,
    e.prazo_operacional,
    e.bloqueio_motivo,
    e.descricao_operacional,
    COALESCE(e.ordem_kanban, pa.ordem_exibicao) AS ordem_kanban,
    COALESCE(e.arquivado, FALSE) AS arquivado,
    (
        SELECT COUNT(*)::int
        FROM diagnostico_plano_acao_comentario c
        WHERE c.plano_acao_id = pa.id AND c.tenant_id = pa.tenant_id
    ) AS comentarios_total,
    (
        SELECT COUNT(*)::int
        FROM diagnostico_plano_subtarefa s
        WHERE s.plano_acao_id = pa.id AND s.tenant_id = pa.tenant_id
    ) AS subtarefas_total
FROM diagnostico_plano_acao pa
LEFT JOIN diagnostico_plano_acao_estado e ON e.plano_acao_id = pa.id
"""


def _pg(value: UUID | None) -> str | None:
    return None if value is None else str(value)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return date.fromisoformat(str(value)[:10])


def _row_to_card(row: dict[str, Any]) -> PlanoAcaoKanbanCard:
    fi = int(row["frente_indice"])
    ai = int(row["acao_indice"])
    return PlanoAcaoKanbanCard(
        plano_acao_id=row["plano_acao_id"],
        diagnostico_id=row["diagnostico_id"],
        tenant_id=row["tenant_id"],
        frente_indice=fi,
        frente_nome=str(row["frente_nome"]),
        acao_indice=ai,
        texto_acao=str(row["texto_acao"]),
        responsavel_sugerido=row.get("responsavel_sugerido"),
        prioridade_motor=int(row["prioridade_motor"]),
        criticidade=row.get("criticidade"),
        base_legal=row.get("base_legal"),
        fase_pdca=row.get("fase_pdca"),
        horizonte_planejado=row.get("horizonte_planejado"),
        chave_quadro_legado=f"f{fi}_a{ai}",
        status_execucao=StatusExecucaoPlanoAcao(str(row["status_execucao"])),
        responsavel_operacional=row.get("responsavel_operacional"),
        prazo_operacional=_parse_date(row.get("prazo_operacional")),
        bloqueio_motivo=row.get("bloqueio_motivo"),
        descricao_operacional=row.get("descricao_operacional"),
        ordem_kanban=int(row["ordem_kanban"]),
        arquivado=bool(row["arquivado"]),
        comentarios_total=int(row["comentarios_total"]),
        subtarefas_total=int(row["subtarefas_total"]),
    )


def _row_to_comentario(row: dict[str, Any]) -> PlanoAcaoComentarioRegistro:
    return PlanoAcaoComentarioRegistro(
        id=row["id"],
        plano_acao_id=row["plano_acao_id"],
        diagnostico_id=row["diagnostico_id"],
        tenant_id=row["tenant_id"],
        autor_label=str(row["autor_label"]),
        autor_email=row.get("autor_email"),
        autor_user_id=row.get("autor_user_id"),
        comentario=str(row["comentario"]),
        sha256_payload=str(row["sha256_payload"]),
        criado_em=row["criado_em"],
    )


def _listar_board_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    incluir_arquivados: bool,
) -> PlanoAcaoKanbanBoard:
    filtro_arq = "" if incluir_arquivados else " AND COALESCE(e.arquivado, FALSE) = FALSE"
    sql = (
        _SELECT_CARD_BASE
        + f"""
WHERE pa.diagnostico_id = %s AND pa.tenant_id = %s
{filtro_arq}
ORDER BY pa.frente_indice ASC, ordem_kanban ASC, pa.acao_indice ASC
"""
    )
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (_pg(diagnostico_id), _pg(tenant_id)))
            rows = cur.fetchall()
        cards = tuple(_row_to_card(cast("dict[str, Any]", r)) for r in rows)
        return PlanoAcaoKanbanBoard(
            diagnostico_id=diagnostico_id,
            tenant_id=tenant_id,
            cards=cards,
        )
    finally:
        conn.close()


def _plano_pertence_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
) -> bool:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM diagnostico_plano_acao
                WHERE id = %s AND diagnostico_id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def _buscar_card_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
) -> PlanoAcaoKanbanCard | None:
    sql = _SELECT_CARD_BASE + """
WHERE pa.id = %s AND pa.diagnostico_id = %s AND pa.tenant_id = %s
LIMIT 1
"""
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)))
            raw = cur.fetchone()
        if raw is None:
            return None
        return _row_to_card(cast("dict[str, Any]", raw))
    finally:
        conn.close()


def _atualizar_estado_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
    dados: AtualizarEstadoKanbanInput,
) -> PlanoAcaoKanbanCard:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT ordem_exibicao, responsavel_sugerido
                FROM diagnostico_plano_acao
                WHERE id = %s AND diagnostico_id = %s AND tenant_id = %s
                """,
                (_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)),
            )
            pa_row = cur.fetchone()
            if pa_row is None:
                raise ValueError("plano_acao_id inexistente")

            cur.execute(
                """
                INSERT INTO diagnostico_plano_acao_estado (
                    plano_acao_id, diagnostico_id, tenant_id,
                    status_execucao, ordem_kanban, responsavel_operacional
                ) VALUES (%s, %s, %s, 'pendente', %s, %s)
                ON CONFLICT (plano_acao_id) DO NOTHING
                """,
                (
                    _pg(plano_acao_id),
                    _pg(diagnostico_id),
                    _pg(tenant_id),
                    int(pa_row["ordem_exibicao"]),
                    pa_row.get("responsavel_sugerido"),
                ),
            )

            sets: list[str] = []
            params: list[Any] = []
            if dados.status_execucao is not None:
                sets.append("status_execucao = %s")
                params.append(dados.status_execucao.value)
            if dados.responsavel_operacional is not None:
                sets.append("responsavel_operacional = %s")
                params.append(dados.responsavel_operacional)
            if dados.prazo_operacional is not None:
                sets.append("prazo_operacional = %s")
                params.append(dados.prazo_operacional)
            elif dados.limpar_prazo:
                sets.append("prazo_operacional = NULL")
            if dados.bloqueio_motivo is not None:
                sets.append("bloqueio_motivo = %s")
                params.append(dados.bloqueio_motivo)
            elif dados.limpar_bloqueio:
                sets.append("bloqueio_motivo = NULL")
            if dados.descricao_operacional is not None:
                sets.append("descricao_operacional = %s")
                params.append(dados.descricao_operacional)
            if dados.ordem_kanban is not None:
                sets.append("ordem_kanban = %s")
                params.append(dados.ordem_kanban)

            if sets:
                params.extend([_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)])
                cur.execute(
                    f"""
                    UPDATE diagnostico_plano_acao_estado
                    SET {", ".join(sets)}
                    WHERE plano_acao_id = %s
                      AND diagnostico_id = %s
                      AND tenant_id = %s
                    """,
                    params,
                )
            conn.commit()

        card = _buscar_card_sync(
            dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
        )
        if card is None:
            raise ValueError("card não encontrado após atualização")
        return card
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _definir_arquivado_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
    arquivado: bool,
) -> PlanoAcaoKanbanCard:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_plano_acao_estado (
                    plano_acao_id, diagnostico_id, tenant_id, status_execucao
                ) VALUES (%s, %s, %s, 'pendente')
                ON CONFLICT (plano_acao_id) DO NOTHING
                """,
                (_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)),
            )
            cur.execute(
                """
                UPDATE diagnostico_plano_acao_estado
                SET arquivado = %s
                WHERE plano_acao_id = %s
                  AND diagnostico_id = %s
                  AND tenant_id = %s
                """,
                (arquivado, _pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id)),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    card = _buscar_card_sync(
        dsn,
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        plano_acao_id=plano_acao_id,
    )
    if card is None:
        raise ValueError("card não encontrado após arquivar")
    return card


def _inserir_comentario_sync(
    dsn: str,
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
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_plano_acao_comentario (
                    plano_acao_id, diagnostico_id, tenant_id,
                    autor_label, autor_email, autor_user_id,
                    comentario, sha256_payload, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    _pg(plano_acao_id),
                    _pg(diagnostico_id),
                    _pg(tenant_id),
                    autor_label,
                    autor_email,
                    _pg(autor_user_id),
                    comentario,
                    sha256_payload.lower(),
                    criado_em,
                ),
            )
            raw = cur.fetchone()
            conn.commit()
        return _row_to_comentario(cast("dict[str, Any]", raw))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _listar_comentarios_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
    limite: int,
) -> tuple[PlanoAcaoComentarioRegistro, ...]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM diagnostico_plano_acao_comentario
                WHERE plano_acao_id = %s
                  AND diagnostico_id = %s
                  AND tenant_id = %s
                ORDER BY criado_em DESC
                LIMIT %s
                """,
                (_pg(plano_acao_id), _pg(diagnostico_id), _pg(tenant_id), limite),
            )
            rows = cur.fetchall()
        return tuple(_row_to_comentario(cast("dict[str, Any]", r)) for r in rows)
    finally:
        conn.close()


class PostgresPlanoAcaoKanbanAdapter(PlanoAcaoKanbanPort):
    """Adapter concreto via psycopg2 síncrono."""

    def __init__(self, *, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def listar_board(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        incluir_arquivados: bool = False,
    ) -> PlanoAcaoKanbanBoard:
        return await asyncio.to_thread(
            _listar_board_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            incluir_arquivados=incluir_arquivados,
        )

    async def plano_acao_pertence_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
    ) -> bool:
        return await asyncio.to_thread(
            _plano_pertence_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
        )

    async def atualizar_estado(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        dados: AtualizarEstadoKanbanInput,
    ) -> PlanoAcaoKanbanCard:
        try:
            return await asyncio.to_thread(
                _atualizar_estado_sync,
                self._dsn,
                tenant_id=tenant_id,
                diagnostico_id=diagnostico_id,
                plano_acao_id=plano_acao_id,
                dados=dados,
            )
        except psycopg2.Error as exc:
            logger.error("kanban_atualizar_estado_falhou", erro=str(exc), exc_info=True)
            raise

    async def definir_arquivado(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        arquivado: bool,
    ) -> PlanoAcaoKanbanCard:
        return await asyncio.to_thread(
            _definir_arquivado_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
            arquivado=arquivado,
        )

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
        return await asyncio.to_thread(
            _inserir_comentario_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
            autor_label=autor_label,
            autor_email=autor_email,
            autor_user_id=autor_user_id,
            comentario=comentario,
            sha256_payload=sha256_payload,
            criado_em=criado_em,
        )

    async def listar_comentarios(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        limite: int = 50,
    ) -> tuple[PlanoAcaoComentarioRegistro, ...]:
        return await asyncio.to_thread(
            _listar_comentarios_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
            limite=limite,
        )

    async def buscar_card(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
    ) -> PlanoAcaoKanbanCard | None:
        return await asyncio.to_thread(
            _buscar_card_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            plano_acao_id=plano_acao_id,
        )
