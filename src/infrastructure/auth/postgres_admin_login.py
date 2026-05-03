"""
Lookup de administrador B2B na tabela `admins` do Postgres.

Camada: Infrastructure
Usado quando há ``DATABASE_URL`` (Docker Compose, CI): o login não depende do REST Supabase em :54321.
Mesmo contrato de senha bcrypt que ``passlib`` na rota ``POST /auth/login``.
"""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

import psycopg2
import psycopg2.errors
from psycopg2.extras import RealDictCursor


def buscar_admin_por_email_postgres(email: str, dsn_sync: str) -> dict[str, Any] | None:
    """
    Busca uma linha em `admins` pelo e-mail (case-insensitive).

    Args:
        email: e-mail informado no login.
        dsn_sync: URL `postgresql://...` (sync).

    Returns:
        Dict com chaves id, email, hashed_password, nome, tenant_id, perfil_conta ou None.
    """
    norm = email.strip().lower()
    conn = psycopg2.connect(dsn_sync)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    id::text AS id,
                    email,
                    hashed_password,
                    nome,
                    tenant_id::text AS tenant_id,
                    COALESCE(perfil_conta, 'gratuito') AS perfil_conta
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


def inserir_admin_postgres(
    *,
    email: str,
    hashed_password: str,
    nome: str,
    tenant_id: UUID,
    dsn_sync: str,
    perfil_conta: str = "gratuito",
) -> UUID:
    """
    Insere linha em `admins` e devolve o `id` gerado.

    Raises:
        ValueError: e-mail duplicado (constraint UNIQUE em `email`).
        psycopg2.Error: falha de conexão ou SQL.
    """
    norm_email = email.strip().lower()
    nome_limpo = (nome or "").strip()[:255] or None
    perfil = perfil_conta.strip().lower()
    if perfil not in ("gratuito", "avancado"):
        perfil = "gratuito"
    conn = psycopg2.connect(dsn_sync)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO admins (email, hashed_password, nome, tenant_id, perfil_conta)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (norm_email, hashed_password, nome_limpo, tenant_id, perfil),
            )
            row = cur.fetchone()
        conn.commit()
        if not row or row[0] is None:
            raise RuntimeError("INSERT em admins não retornou id.")
        return UUID(str(row[0]))
    except psycopg2.errors.UniqueViolation as e:
        conn.rollback()
        raise ValueError("Este e-mail já está cadastrado.") from e
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def buscar_email_admin_por_id_e_tenant_postgres(
    admin_id: UUID, tenant_id: UUID, dsn_sync: str
) -> str | None:
    """
    Retorna o e-mail do admin quando `id` e `tenant_id` conferem (defense-in-depth no vincular lead).

    Args:
        admin_id: UUID do registro em `admins` (claim JWT `sub`).
        tenant_id: UUID do tenant (claim JWT `tenant_id`).
        dsn_sync: URL `postgresql://...` (sync).

    Returns:
        E-mail normalizado em minúsculas ou None se não existir linha compatível.
    """
    conn = psycopg2.connect(dsn_sync)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT lower(trim(email)) AS email
                FROM admins
                WHERE id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (admin_id, tenant_id),
            )
            row = cur.fetchone()
            if not row:
                return None
            em = row.get("email")
            return str(em).strip().lower() if em is not None else None
    finally:
        conn.close()
