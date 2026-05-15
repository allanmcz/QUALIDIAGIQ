"""
Histórico append-only de explicações LLM (PostgreSQL síncrono).

Camada: Infrastructure
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import psycopg2

if TYPE_CHECKING:
    from uuid import UUID
from psycopg2.extras import Json, RealDictCursor


def inserir_explicacao_score_llm_historico_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    snapshot: dict[str, Any],
    actor_user_id: UUID | None,
    trace_id: str | None,
) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_explicacao_score_llm_historico (
                    tenant_id, diagnostico_id, snapshot, actor_user_id, trace_id
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(tenant_id),
                    str(diagnostico_id),
                    Json(snapshot),
                    str(actor_user_id) if actor_user_id else None,
                    (trace_id or "")[:128] or None,
                ),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def listar_explicacao_score_llm_historico_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    limit: int = 20,
) -> list[dict[str, Any]]:
    lim = max(1, min(limit, 100))
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT snapshot, actor_user_id, trace_id, criado_em
                FROM diagnostico_explicacao_score_llm_historico
                WHERE tenant_id = %s AND diagnostico_id = %s
                ORDER BY criado_em DESC
                LIMIT %s
                """,
                (str(tenant_id), str(diagnostico_id), lim),
            )
            rows = cur.fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            snap = row.get("snapshot")
            if isinstance(snap, str):
                snap = json.loads(snap)
            if not isinstance(snap, dict):
                continue
            item = dict(snap)
            item["gerado_em"] = row.get("criado_em")
            item["trace_id"] = row.get("trace_id")
            item["actor_user_id"] = (
                str(row["actor_user_id"]) if row.get("actor_user_id") is not None else None
            )
            out.append(item)
        return out
    finally:
        conn.close()
