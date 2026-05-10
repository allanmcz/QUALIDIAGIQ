"""
Rotas HTTP de manutenção operacional (camada Presentation).

Fallback quando pg_cron não está disponível no cluster: limpeza explícita da cache
idempotente via SQL `qdi_cleanup_idempotency()`.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Annotated

import psycopg2
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.infrastructure.config.settings import get_settings
from src.presentation.api.dependencies import require_perfil_manutencao_plataforma

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin/maintenance", tags=["Manutenção"])

_RATE_LOCK = threading.Lock()
_LAST_CLEANUP_TS_BY_TENANT: dict[uuid.UUID, float] = {}
_CLEANUP_COOLDOWN_SEC = 300.0


class CleanupIdempotencyResponse(BaseModel):
    """Resultado da rotina de limpeza."""

    deleted_count: int = Field(ge=0, description="Linhas removidas de idempotency_responses.")
    executed_at: str = Field(description="Instante de execução (ISO 8601).")


def _rate_limit_ok(tenant_id: uuid.UUID) -> bool:
    now = time.monotonic()
    with _RATE_LOCK:
        last = _LAST_CLEANUP_TS_BY_TENANT.get(tenant_id, 0.0)
        if now - last < _CLEANUP_COOLDOWN_SEC:
            return False
        _LAST_CLEANUP_TS_BY_TENANT[tenant_id] = now
        return True


@router.post(
    "/cleanup-idempotency",
    response_model=CleanupIdempotencyResponse,
    summary="Limpar respostas idempotentes expiradas",
    description=(
        "Executa `SELECT * FROM qdi_cleanup_idempotency()` no Postgres. "
        "Máximo **1 chamada a cada 5 minutos** por `tenant_id` do JWT. "
        "Exige perfil **admin** ou **avançado**."
    ),
)
async def cleanup_idempotency(
    current: Annotated[
        tuple[uuid.UUID, uuid.UUID, str],
        Depends(require_perfil_manutencao_plataforma),
    ],
) -> CleanupIdempotencyResponse:
    user_id, tenant_id, perfil = current
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL não configurado — limpeza exige Postgres.",
        )
    if not _rate_limit_ok(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Aguarde 5 minutos entre execuções para este tenant.",
        )

    log = logger.bind(
        tenant_id=str(tenant_id),
        user_id=str(user_id),
        perfil_conta=perfil,
    )
    conn = None
    deleted_count = 0
    executed_at_iso = ""
    try:
        conn = psycopg2.connect(dsn)
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM qdi_cleanup_idempotency()")
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("qdi_cleanup_idempotency sem retorno")
            deleted_count = int(row[0])
            ts = row[1]
            executed_at_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
    except Exception as e:
        if conn is None:
            log.error("cleanup_idempotency_db_connect_falhou", erro=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao conectar ao Postgres.",
            ) from e
        log.error("cleanup_idempotency_exec_falhou", erro=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao executar limpeza.",
        ) from e
    finally:
        if conn is not None:  # pragma: no branch
            conn.close()

    log.info(
        "cleanup_idempotency_ok",
        deleted_count=deleted_count,
        executed_at=executed_at_iso,
    )
    return CleanupIdempotencyResponse(
        deleted_count=deleted_count,
        executed_at=executed_at_iso,
    )


__all__ = ["router"]
