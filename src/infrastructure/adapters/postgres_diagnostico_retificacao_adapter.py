"""
Adapter Postgres para retificações de diagnóstico.

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.application.ports.diagnostico_retificacao_port import (
    DiagnosticoRetificacaoPort,
    DiagnosticoRetificacaoRegisto,
)


def _row_para_model(row: dict[str, Any]) -> DiagnosticoRetificacaoRegisto:
    raw_criado = row["criado_em"]
    criado_em = datetime.fromisoformat(str(raw_criado).replace("Z", "+00:00"))
    payload = row.get("payload_retificacao")
    if not isinstance(payload, dict):
        payload = {}
    actor = row.get("actor_user_id")
    return DiagnosticoRetificacaoRegisto(
        id=UUID(str(row["id"])),
        tenant_id=UUID(str(row["tenant_id"])),
        diagnostico_original_id=UUID(str(row["diagnostico_original_id"])),
        hash_diagnostico_original_sha256=str(row["hash_diagnostico_original_sha256"]),
        motivo_retificacao=str(row["motivo_retificacao"]),
        payload_retificacao=payload,
        hash_retificacao_sha256=str(row["hash_retificacao_sha256"]),
        actor_user_id=UUID(str(actor)) if actor else None,
        criado_em=criado_em.astimezone(UTC),
    )


def _inserir_sync(
    dsn: str,
    *,
    retificacao_id: UUID,
    tenant_id: UUID,
    diagnostico_original_id: UUID,
    hash_diagnostico_original_sha256: str,
    motivo_retificacao: str,
    payload_retificacao: dict[str, Any],
    hash_retificacao_sha256: str,
    actor_user_id: UUID | None,
) -> DiagnosticoRetificacaoRegisto:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_retificacao (
                    id, tenant_id, diagnostico_original_id,
                    hash_diagnostico_original_sha256, motivo_retificacao,
                    payload_retificacao, hash_retificacao_sha256, actor_user_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    str(retificacao_id),
                    str(tenant_id),
                    str(diagnostico_original_id),
                    hash_diagnostico_original_sha256.lower(),
                    motivo_retificacao,
                    Json(payload_retificacao),
                    hash_retificacao_sha256.lower(),
                    str(actor_user_id) if actor_user_id else None,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            raise RuntimeError("INSERT retificação sem RETURNING")
        return _row_para_model(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _listar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_original_id: UUID,
    limit: int,
) -> list[DiagnosticoRetificacaoRegisto]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM diagnostico_retificacao
                WHERE tenant_id = %s AND diagnostico_original_id = %s
                ORDER BY criado_em DESC
                LIMIT %s
                """,
                (str(tenant_id), str(diagnostico_original_id), limit),
            )
            rows = cur.fetchall()
        return [_row_para_model(cast("dict[str, Any]", dict(r))) for r in rows]
    finally:
        conn.close()


class PostgresDiagnosticoRetificacaoAdapter(DiagnosticoRetificacaoPort):
    """Implementação síncrona sob ``asyncio.to_thread``."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def inserir(
        self,
        *,
        retificacao_id: UUID,
        tenant_id: UUID,
        diagnostico_original_id: UUID,
        hash_diagnostico_original_sha256: str,
        motivo_retificacao: str,
        payload_retificacao: dict[str, Any],
        hash_retificacao_sha256: str,
        actor_user_id: UUID | None,
    ) -> DiagnosticoRetificacaoRegisto:
        return await asyncio.to_thread(
            _inserir_sync,
            self._dsn,
            retificacao_id=retificacao_id,
            tenant_id=tenant_id,
            diagnostico_original_id=diagnostico_original_id,
            hash_diagnostico_original_sha256=hash_diagnostico_original_sha256,
            motivo_retificacao=motivo_retificacao,
            payload_retificacao=payload_retificacao,
            hash_retificacao_sha256=hash_retificacao_sha256,
            actor_user_id=actor_user_id,
        )

    async def listar_por_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_original_id: UUID,
        limit: int,
    ) -> list[DiagnosticoRetificacaoRegisto]:
        return await asyncio.to_thread(
            _listar_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_original_id=diagnostico_original_id,
            limit=limit,
        )
