"""
Adapter Postgres para ``LgpdTitularSolicitacaoPort``.

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from typing import Any, cast
from uuid import UUID

import psycopg2
import structlog
from psycopg2.extras import Json, RealDictCursor

from src.application.errors import ErroPersistenciaLgpdError
from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)

logger = structlog.get_logger(__name__)


def _pg_uuid(value: UUID | None) -> str | None:
    """psycopg2 não adapta ``uuid.UUID`` nativamente — serializar como texto."""
    return None if value is None else str(value)


def _from_row(row: dict[str, Any]) -> SolicitacaoTitular:
    return SolicitacaoTitular(
        id=row["id"],
        tenant_id=row["tenant_id"],
        diagnostico_id=row["diagnostico_id"],
        tipo=TipoSolicitacaoTitular(str(row["tipo"])),
        status=StatusSolicitacaoTitular(str(row["status"])),
        canal=CanalSolicitacaoTitular(str(row["canal"])),
        solicitante_email=str(row["solicitante_email"]),
        payload=cast("dict[str, Any]", row["payload"] or {}),
        observacao_interna=row.get("observacao_interna"),
        actor_user_id=row.get("actor_user_id"),
        criado_em=row["criado_em"],
        atualizado_em=row["atualizado_em"],
    )


def _buscar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    solicitacao_id: UUID,
) -> SolicitacaoTitular | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM lgpd_titular_solicitacao
                WHERE id = %s
                  AND tenant_id = %s
                """,
                (_pg_uuid(solicitacao_id), _pg_uuid(tenant_id)),
            )
            raw = cur.fetchone()
        if raw is None:
            return None
        return _from_row(cast("dict[str, Any]", raw))
    finally:
        conn.close()


def _criar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID | None,
    tipo: str,
    canal: str,
    solicitante_email: str,
    payload: dict[str, Any],
    actor_user_id: UUID | None,
) -> SolicitacaoTitular:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO lgpd_titular_solicitacao (
                    tenant_id,
                    diagnostico_id,
                    tipo,
                    status,
                    canal,
                    solicitante_email,
                    payload,
                    actor_user_id
                ) VALUES (%s, %s, %s, 'recebida', %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    _pg_uuid(tenant_id),
                    _pg_uuid(diagnostico_id),
                    tipo,
                    canal,
                    solicitante_email,
                    Json(payload),
                    _pg_uuid(actor_user_id),
                ),
            )
            raw = cur.fetchone()
        conn.commit()
        if raw is None:
            raise RuntimeError("Falha ao criar solicitação LGPD (retorno vazio).")
        return _from_row(cast("dict[str, Any]", raw))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _listar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    status: str | None,
    limit: int,
) -> list[SolicitacaoTitular]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status is None:
                cur.execute(
                    """
                    SELECT *
                    FROM lgpd_titular_solicitacao
                    WHERE tenant_id = %s
                    ORDER BY criado_em DESC
                    LIMIT %s
                    """,
                    (_pg_uuid(tenant_id), limit),
                )
            else:
                cur.execute(
                    """
                    SELECT *
                    FROM lgpd_titular_solicitacao
                    WHERE tenant_id = %s
                      AND status = %s
                    ORDER BY criado_em DESC
                    LIMIT %s
                    """,
                    (_pg_uuid(tenant_id), status, limit),
                )
            rows = cast("list[dict[str, Any]]", cur.fetchall())
        return [_from_row(row) for row in rows]
    finally:
        conn.close()


def _atualizar_status_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    solicitacao_id: UUID,
    status: str,
    observacao_interna: str | None,
    actor_user_id: UUID | None,
) -> SolicitacaoTitular | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE lgpd_titular_solicitacao
                SET status = %s,
                    observacao_interna = %s,
                    actor_user_id = %s
                WHERE id = %s
                  AND tenant_id = %s
                RETURNING *
                """,
                (
                    status,
                    observacao_interna,
                    _pg_uuid(actor_user_id),
                    _pg_uuid(solicitacao_id),
                    _pg_uuid(tenant_id),
                ),
            )
            raw = cur.fetchone()
        conn.commit()
        if raw is None:
            return None
        return _from_row(cast("dict[str, Any]", raw))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresLgpdTitularSolicitacaoAdapter(LgpdTitularSolicitacaoPort):
    """Persistência síncrona via psycopg2 encapsulada em ``asyncio.to_thread``."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def buscar_por_id(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
    ) -> SolicitacaoTitular | None:
        return await asyncio.to_thread(
            _buscar_sync,
            self._dsn,
            tenant_id=tenant_id,
            solicitacao_id=solicitacao_id,
        )

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
        return await asyncio.to_thread(
            _criar_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            tipo=tipo.value,
            canal=canal.value,
            solicitante_email=solicitante_email,
            payload=payload,
            actor_user_id=actor_user_id,
        )

    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        status: StatusSolicitacaoTitular | None,
        limit: int,
    ) -> list[SolicitacaoTitular]:
        try:
            return await asyncio.to_thread(
                _listar_sync,
                self._dsn,
                tenant_id=tenant_id,
                status=status.value if status is not None else None,
                limit=limit,
            )
        except psycopg2.Error as exc:
            logger.error("lgpd_listar_por_tenant_falhou", erro=str(exc), exc_info=True)
            raise ErroPersistenciaLgpdError(
                "Não foi possível listar pedidos LGPD. Verifique migração 0028 (tabela lgpd_titular_solicitacao), "
                "DATABASE_URL síncrono e conectividade com o Postgres."
            ) from exc

    async def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
        status: StatusSolicitacaoTitular,
        observacao_interna: str | None,
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular | None:
        return await asyncio.to_thread(
            _atualizar_status_sync,
            self._dsn,
            tenant_id=tenant_id,
            solicitacao_id=solicitacao_id,
            status=status.value,
            observacao_interna=observacao_interna,
            actor_user_id=actor_user_id,
        )
