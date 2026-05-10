"""
Adapter Postgres — anonimização respondente (LGPD + WORM).

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.application.ports.lgpd_anonimizacao_executor_port import (
    LgpdAnonimizacaoExecutorPort,
)

if TYPE_CHECKING:
    from uuid import UUID

_CAMPOS_JSON: dict[str, bool] = {
    "respondente_email": True,
    "respondente_nome": True,
    "respondente_cargo": True,
    "respondente_telefone": True,
    "respondente_ip_origem": True,
}


def _aplicar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    solicitacao_id: UUID,
    actor_user_id: UUID,
) -> None:
    anon_email = f"anon+{str(diagnostico_id).replace('-', '')}@invalid.qdi"
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT status
                FROM diagnosticos
                WHERE id = %s
                  AND tenant_id = %s
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError("Diagnóstico não encontrado para o tenant.")
            if str(row["status"]) != "finalizado":
                raise ValueError(
                    "Somente diagnóstico finalizado admite anonimização controlada pelo trigger WORM."
                )

            cur.execute(
                """
                INSERT INTO lgpd_anonimizacao_log (
                    tenant_id,
                    solicitacao_id,
                    diagnostico_id,
                    actor_user_id,
                    campos_afetados
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    str(tenant_id),
                    str(solicitacao_id),
                    str(diagnostico_id),
                    str(actor_user_id),
                    Json(_CAMPOS_JSON),
                ),
            )

            cur.execute(
                """
                UPDATE diagnosticos
                SET respondente_email = %s,
                    respondente_nome = %s,
                    respondente_cargo = NULL,
                    respondente_telefone = NULL,
                    respondente_ip_origem = NULL
                WHERE id = %s
                  AND tenant_id = %s
                """,
                (anon_email, "[anonimizado]", str(diagnostico_id), str(tenant_id)),
            )
            if cur.rowcount != 1:
                raise RuntimeError("Falha ao anonimizar diagnóstico (rowcount != 1).")

            cur.execute(
                """
                UPDATE lgpd_titular_solicitacao
                SET status = 'concluida',
                    actor_user_id = %s,
                    observacao_interna = COALESCE(
                        observacao_interna,
                        'Anonimização respondente executada via API.'
                    )
                WHERE id = %s
                  AND tenant_id = %s
                  AND status = 'deferida'
                """,
                (str(actor_user_id), str(solicitacao_id), str(tenant_id)),
            )
            if cur.rowcount != 1:
                raise ValueError(
                    "Solicitação não está deferida ou não pertence ao tenant — nada foi concluído."
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresLgpdAnonimizacaoExecutorAdapter(LgpdAnonimizacaoExecutorPort):
    """Transação síncrona em thread pool — conexão com privilégios de escrita no DDL QDI."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def aplicar_anonimizacao_respondente(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        await asyncio.to_thread(
            _aplicar_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            solicitacao_id=solicitacao_id,
            actor_user_id=actor_user_id,
        )
