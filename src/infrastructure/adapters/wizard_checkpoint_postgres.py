"""
Adapter Postgres para checkpoints LangGraph do wizard.

Camada: Infrastructure — Fase H Onda IA 1.1.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import asyncpg
import structlog

from src.application.ports.wizard_checkpoint_port import WizardCheckpointPort

logger = structlog.get_logger(__name__)


class PostgresWizardCheckpointAdapter(WizardCheckpointPort):
    """Persiste em ``qdi.wizard_langgraph_checkpoint`` com RLS por tenant."""

    def __init__(self, dsn: str, *, connect_timeout_seconds: float = 10.0) -> None:
        self._dsn = dsn.strip().replace("postgresql+asyncpg://", "postgresql://", 1)
        self._connect_timeout = connect_timeout_seconds

    async def salvar(
        self,
        thread_id: UUID,
        tenant_id: UUID,
        checkpoint: dict[str, Any],
    ) -> None:
        payload = json.dumps(checkpoint, ensure_ascii=False)
        conn = await asyncpg.connect(self._dsn, timeout=self._connect_timeout)
        try:
            await conn.execute(
                """
                INSERT INTO qdi.wizard_langgraph_checkpoint (thread_id, tenant_id, checkpoint)
                VALUES ($1, $2, $3::jsonb)
                ON CONFLICT (thread_id) DO UPDATE SET
                    tenant_id = EXCLUDED.tenant_id,
                    checkpoint = EXCLUDED.checkpoint,
                    atualizado_em = now()
                """,
                thread_id,
                tenant_id,
                payload,
            )
        except Exception as exc:
            logger.error(
                "wizard_checkpoint_salvar_falhou",
                thread_id=str(thread_id),
                tenant_id=str(tenant_id),
                erro=str(exc),
                exc_info=True,
            )
            raise
        finally:
            await conn.close()

    async def carregar(
        self,
        thread_id: UUID,
        tenant_id: UUID,
    ) -> dict[str, Any] | None:
        conn = await asyncpg.connect(self._dsn, timeout=self._connect_timeout)
        try:
            row = await conn.fetchrow(
                """
                SELECT checkpoint
                FROM qdi.wizard_langgraph_checkpoint
                WHERE thread_id = $1 AND tenant_id = $2
                """,
                thread_id,
                tenant_id,
            )
        except Exception as exc:
            logger.warning(
                "wizard_checkpoint_carregar_falhou",
                thread_id=str(thread_id),
                erro=str(exc),
                exc_info=True,
            )
            return None
        finally:
            await conn.close()
        if row is None:
            return None
        raw = row["checkpoint"]
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            return json.loads(raw)
        return dict(raw)

    async def remover(self, thread_id: UUID, tenant_id: UUID) -> bool:
        conn = await asyncpg.connect(self._dsn, timeout=self._connect_timeout)
        try:
            tag = await conn.execute(
                """
                DELETE FROM qdi.wizard_langgraph_checkpoint
                WHERE thread_id = $1 AND tenant_id = $2
                """,
                thread_id,
                tenant_id,
            )
        except Exception as exc:
            logger.warning(
                "wizard_checkpoint_remover_falhou",
                thread_id=str(thread_id),
                erro=str(exc),
                exc_info=True,
            )
            return False
        finally:
            await conn.close()
        return tag.endswith("1")
