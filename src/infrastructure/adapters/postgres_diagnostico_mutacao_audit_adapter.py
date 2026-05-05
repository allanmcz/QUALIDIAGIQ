"""
Adapter Postgres para ``DiagnosticoMutacaoAuditPort`` (INSERT síncrono em thread pool).

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

import psycopg2
from psycopg2.extras import Json

from src.application.ports.diagnostico_mutacao_audit_port import (
    DiagnosticoMutacaoAuditPort,
    TipoMutacaoDiagnostico,
)


def _insert_audit_sync(
    dsn: str,
    tenant_id: UUID,
    diagnostico_id: UUID,
    tipo: str,
    payload: dict[str, Any],
    actor_user_id: UUID | None,
    versao_otimista_antes: int,
    versao_otimista_apos: int,
) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_mutacao_audit (
                    tenant_id,
                    diagnostico_id,
                    tipo,
                    payload,
                    actor_user_id,
                    versao_otimista_antes,
                    versao_otimista_apos
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    tenant_id,
                    diagnostico_id,
                    tipo,
                    Json(payload),
                    actor_user_id,
                    versao_otimista_antes,
                    versao_otimista_apos,
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresDiagnosticoMutacaoAuditAdapter(DiagnosticoMutacaoAuditPort):
    """Grava em ``public.diagnostico_mutacao_audit`` via ``asyncio.to_thread``."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def registrar(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        tipo: TipoMutacaoDiagnostico,
        payload: dict[str, Any],
        actor_user_id: UUID | None,
        versao_otimista_antes: int,
        versao_otimista_apos: int,
    ) -> None:
        await asyncio.to_thread(
            _insert_audit_sync,
            self._dsn,
            tenant_id,
            diagnostico_id,
            tipo.value,
            payload,
            actor_user_id,
            versao_otimista_antes,
            versao_otimista_apos,
        )
