"""
Persistência de rascunhos self-service (payload até OTP / conta na plataforma).

Camada: Infrastructure — SQL síncrono (psycopg2), invocado via asyncio.to_thread a partir das rotas.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

_RASCUNHO_TTL_HORAS = 24


def _token_sha256(token_plain: str) -> str:
    return hashlib.sha256(token_plain.encode("utf-8")).hexdigest()


def inserir_rascunho_sync(
    dsn: str,
    *,
    tenant_id: UUID,
    email_norm: str,
    payload_dict: dict[str, Any],
) -> tuple[str, datetime, UUID]:
    """
    Insere rascunho e devolve (token em texto claro uma única vez, expira_em UTC, id da linha).

    O ``id`` permite correlação em logs (QDI-H-022) sem expor o token opaco.
    """
    token_plain = secrets.token_urlsafe(32)
    th = _token_sha256(token_plain)
    expira = datetime.now(UTC) + timedelta(hours=_RASCUNHO_TTL_HORAS)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_rascunhos_self_service (
                    tenant_id, email_norm, payload_json, token_sha256, expira_em
                ) VALUES (%s, %s, %s::jsonb, %s, %s)
                RETURNING id
                """,
                (str(tenant_id), email_norm, Json(payload_dict), th, expira),
            )
            row = cur.fetchone()
            if not row or row[0] is None:
                raise RuntimeError("INSERT rascunho self-service sem RETURNING id.")
            rascunho_id = UUID(str(row[0]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return token_plain, expira, rascunho_id


def buscar_rascunho_ativo_por_token_sync(dsn: str, token_plain: str) -> dict[str, Any] | None:
    """Linha ativa (não consumida, não expirada) ou None."""
    th = _token_sha256(token_plain.strip())
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, tenant_id, email_norm, payload_json, expira_em, consumido_em
                FROM diagnostico_rascunhos_self_service
                WHERE token_sha256 = %s
                LIMIT 1
                """,
                (th,),
            )
            row = cur.fetchone()
        if not row:
            return None
        r = cast("dict[str, Any]", dict(row))
        if r.get("consumido_em") is not None:
            return None
        exp = r.get("expira_em")
        if exp is None:
            # Esquema exige NOT NULL; se vier nulo (corrupção/migração), não devolver linha ativa.
            return None
        exp_dt = (
            exp
            if isinstance(exp, datetime)
            else datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
        )
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=UTC)
        if datetime.now(UTC) > exp_dt:
            return None
        return r
    finally:
        conn.close()


def marcar_rascunho_consumido_sync(dsn: str, rascunho_id: UUID) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE diagnostico_rascunhos_self_service
                SET consumido_em = CURRENT_TIMESTAMP
                WHERE id = %s AND consumido_em IS NULL
                """,
                (str(rascunho_id),),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
