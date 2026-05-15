"""
Quotas diárias de uso LLM por tenant (ADR-022 Fase 4 — MVP).

Camada: Infrastructure — contagem via ``llm_tenant_usage_ledger``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import psycopg2

if TYPE_CHECKING:
    from uuid import UUID


class LlmQuotaExcedidaError(Exception):
    """Limite diário de chamadas LLM atingido para o tenant."""


def assert_quota_disponivel_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    task_type: str,
    limite_diario: int,
) -> None:
    """Raises LlmQuotaExcedidaError se o limite diário já foi atingido."""
    if limite_diario <= 0:
        return
    count = contar_uso_llm_hoje_sync(dsn, tenant_id=tenant_id, task_type=task_type)
    if count >= limite_diario:
        raise LlmQuotaExcedidaError(
            f"Quota diária de LLM ({task_type}) atingida: {limite_diario} por tenant."
        )


def registrar_uso_llm_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    task_type: str,
    trace_id: str | None = None,
) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO llm_tenant_usage_ledger (tenant_id, task_type, trace_id)
                VALUES (%s, %s, %s)
                """,
                (str(tenant_id), task_type[:48], (trace_id or "")[:128] or None),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def contar_uso_llm_hoje_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    task_type: str,
) -> int:
    """Contagem para health/dashboard (sem side-effect)."""
    inicio_dia = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)::int
                FROM llm_tenant_usage_ledger
                WHERE tenant_id = %s AND task_type = %s AND criado_em >= %s
                """,
                (str(tenant_id), task_type[:48], inicio_dia),
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0
    finally:
        conn.close()
