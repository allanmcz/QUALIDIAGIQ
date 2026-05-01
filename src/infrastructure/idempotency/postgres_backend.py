"""
Persistência de idempotência em PostgreSQL (SQLAlchemy sync).

Usada pelo middleware quando `DATABASE_URL` está definida (URL sync `postgresql://`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import text

from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def idempotency_get(engine: Engine, chave_hash: str) -> CorpoCacheadoIdempotencia | None:
    """Recupera corpo cacheado se existir e não expirou."""
    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    "SELECT status_code, body, headers_json FROM idempotency_responses "
                    "WHERE chave_hash = :h AND expira_em > now()"
                ),
                {"h": chave_hash},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        hj = row["headers_json"]
        tup = tuple((str(k), str(v)) for k, v in hj.items()) if isinstance(hj, dict) else ()
        body_raw = row["body"]
        body_b = body_raw if isinstance(body_raw, bytes) else bytes(body_raw)
        return CorpoCacheadoIdempotencia(
            status_code=int(row["status_code"]),
            body=body_b,
            headers=tup,
        )


def idempotency_put(
    engine: Engine,
    chave_hash: str,
    cached: CorpoCacheadoIdempotencia,
    ttl_seconds: int,
) -> None:
    """Grava ou substitui entrada (upsert por chave_hash)."""
    headers_obj = dict(cached.headers)
    body = cached.body
    expira = datetime.now(UTC) + timedelta(seconds=int(ttl_seconds))
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM idempotency_responses WHERE expira_em < now()"))
        conn.execute(
            text("""
                INSERT INTO idempotency_responses (
                  chave_hash, status_code, body, headers_json, expira_em
                ) VALUES (
                  :h, :sc, :body, CAST(:hdr AS jsonb), :expira
                )
                ON CONFLICT (chave_hash) DO UPDATE SET
                  status_code = EXCLUDED.status_code,
                  body = EXCLUDED.body,
                  headers_json = EXCLUDED.headers_json,
                  expira_em = EXCLUDED.expira_em,
                  criado_em = now()
                """),
            {
                "h": chave_hash,
                "sc": cached.status_code,
                "body": body,
                "hdr": json.dumps(headers_obj),
                "expira": expira,
            },
        )


def idempotency_cleanup_expired(engine: Engine) -> None:
    """Remove linhas expiradas (manutenção best-effort)."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM idempotency_responses WHERE expira_em < now()"))
