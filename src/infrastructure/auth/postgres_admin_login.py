"""
Lookup de administrador B2B na tabela `admins` do Postgres.

Camada: Infrastructure
Usado quando há ``DATABASE_URL`` (Docker Compose, CI): o login não depende do REST Supabase em :54321.
Mesmo contrato de senha bcrypt que ``passlib`` na rota ``POST /auth/login``.
"""

from __future__ import annotations

from typing import Any, cast

import psycopg2
from psycopg2.extras import RealDictCursor


def buscar_admin_por_email_postgres(email: str, dsn_sync: str) -> dict[str, Any] | None:
    """
    Busca uma linha em `admins` pelo e-mail (case-insensitive).

    Args:
        email: e-mail informado no login.
        dsn_sync: URL `postgresql://...` (sync).

    Returns:
        Dict com chaves id, email, hashed_password, nome, tenant_id (strings UUID) ou None.
    """
    norm = email.strip().lower()
    conn = psycopg2.connect(dsn_sync)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id::text AS id, email, hashed_password, nome, tenant_id::text AS tenant_id
                FROM admins
                WHERE lower(trim(email)) = %s
                LIMIT 1
                """,
                (norm,),
            )
            row = cur.fetchone()
            return cast("dict[str, Any]", dict(row)) if row else None
    finally:
        conn.close()
