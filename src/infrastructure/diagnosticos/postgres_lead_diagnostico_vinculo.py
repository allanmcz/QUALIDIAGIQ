"""
Reatribuição de tenant em `diagnosticos` via Postgres (sync).

Camada: Infrastructure

Usa a mesma URL sync do login (`postgresql://...`) — no Docker o role `postgres`
efetua UPDATE sem ficar preso às políticas RLS do papel `authenticated` (PostgREST).
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor

from src.application.ports.lead_diagnostico_vinculo_port import LeadDiagnosticoVinculoPort


def vincular_gratuitos_self_service_sync(
    dsn_sync: str,
    *,
    tenant_self_service: UUID,
    tenant_destino: UUID,
    email_admin_normalizado: str,
) -> list[UUID]:
    """
    Atualiza linhas elegíveis e devolve os UUIDs afetados.

    Raises:
        psycopg2.Error: falha de conexão ou SQL.
    """
    email = email_admin_normalizado.strip().lower()
    conn = psycopg2.connect(dsn_sync)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE diagnosticos AS d
                SET tenant_id = %(dest)s
                WHERE d.tenant_id = %(orig)s
                  AND lower(trim(COALESCE(d.respondente_email, ''))) = %(email)s
                  AND lower(trim(COALESCE(d.plano::text, 'gratuito'))) = 'gratuito'
                RETURNING d.id
                """,
                {
                    "dest": str(tenant_destino),
                    "orig": str(tenant_self_service),
                    "email": email,
                },
            )
            rows = cur.fetchall()
        conn.commit()
        out: list[UUID] = []
        for r in rows:
            raw = r.get("id")
            if raw is not None:
                out.append(UUID(str(raw)))
        return out
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresLeadDiagnosticoVinculoAdapter(LeadDiagnosticoVinculoPort):
    """Port adapter: UPDATE via conexão sync (thread pool)."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def vincular_gratuitos_self_service_para_tenant(
        self,
        *,
        email_admin_normalizado: str,
        tenant_destino: UUID,
        tenant_self_service: UUID,
    ) -> list[UUID]:
        return await asyncio.to_thread(
            vincular_gratuitos_self_service_sync,
            self._dsn,
            tenant_self_service=tenant_self_service,
            tenant_destino=tenant_destino,
            email_admin_normalizado=email_admin_normalizado,
        )
