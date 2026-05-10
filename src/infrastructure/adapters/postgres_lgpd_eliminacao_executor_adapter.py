"""
Adapter Postgres — eliminação física de diagnóstico pré-finalização (LGPD).

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import psycopg2
from psycopg2.extras import RealDictCursor

from src.application.errors import EliminacaoDiagnosticoFinalizadoWormError
from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort

if TYPE_CHECKING:
    from uuid import UUID

_STATUSES_ELIMINAVEIS = frozenset({"em_andamento", "cancelado", "expirado"})


def _aplicar_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    diagnostico_id: UUID,
    solicitacao_id: UUID,
    actor_user_id: UUID,
) -> None:
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
            st = str(row["status"])
            if st == "finalizado":
                raise EliminacaoDiagnosticoFinalizadoWormError(
                    "Diagnóstico finalizado: evidência sob WORM — use anonimização do respondente "
                    "(POST /privacidade/diagnosticos/{id}/anonimizar-respondente) em vez de eliminação física."
                )
            if st not in _STATUSES_ELIMINAVEIS:
                raise ValueError(
                    f"Eliminação física não suportada para status '{st}'. Estados admissíveis: "
                    f"{sorted(_STATUSES_ELIMINAVEIS)}."
                )

            cur.execute(
                """
                DELETE FROM diagnosticos
                WHERE id = %s
                  AND tenant_id = %s
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            if cur.rowcount != 1:
                raise RuntimeError("Falha ao eliminar diagnóstico (rowcount != 1).")

            cur.execute(
                """
                UPDATE lgpd_titular_solicitacao
                SET status = 'concluida',
                    actor_user_id = %s,
                    observacao_interna = COALESCE(
                        observacao_interna,
                        'Eliminação física do diagnóstico executada via API (pré-WORM finalizado).'
                    )
                WHERE id = %s
                  AND tenant_id = %s
                  AND status = 'deferida'
                """,
                (str(actor_user_id), str(solicitacao_id), str(tenant_id)),
            )
            if cur.rowcount != 1:
                raise ValueError(
                    "Solicitação não está deferida ou não pertence ao tenant — rollback aplicado."
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresLgpdEliminacaoExecutorAdapter(LgpdEliminacaoExecutorPort):
    """Transação síncrona em thread pool — mesmo DSN dos fluxos LGPD síncronos."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def aplicar_eliminacao_diagnostico(
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
