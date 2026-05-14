#!/usr/bin/env python3
"""
Lista tabelas do schema ``public`` com Row Level Security (RLS) activo.

Uso (uma das opções):
  DATABASE_URL=postgresql://... python scripts/report_rls_public.py
  QDI_POSTGRES_TEST_URL=postgresql://... python scripts/report_rls_public.py
  python scripts/report_rls_public.py postgresql://user:pass@host:5432/db

Aceita URL com prefixo ``postgresql+asyncpg://`` (normaliza para asyncpg).

Saída: relatório em PT-BR no stdout; código de saída 0 = OK, 1 = erro (sem DSN ou falha de conexão).

Camada: ferramenta de operação (fora da Clean Architecture).
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg


def _dsn_normalizado(raw: str) -> str:
    return raw.strip().replace("postgresql+asyncpg://", "postgresql://", 1)


def _parse_argv(argv: list[str]) -> str | None:
    dsn: str | None = None
    for a in argv:
        if not a.startswith("-"):
            dsn = a
    return dsn


async def _listar_rls_public(conn: asyncpg.Connection) -> list[str]:
    rows = await conn.fetch("""
        SELECT c.relname AS table_name
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND c.relrowsecurity IS TRUE
        ORDER BY c.relname
        """)
    return [str(r["table_name"]) for r in rows]


async def _executar(dsn: str) -> list[str]:
    conn = await asyncpg.connect(dsn)
    try:
        return await _listar_rls_public(conn)
    finally:
        await conn.close()


def main() -> int:
    dsn_arg = _parse_argv(sys.argv[1:])
    raw_url = dsn_arg or os.environ.get("DATABASE_URL") or os.environ.get("QDI_POSTGRES_TEST_URL")
    if not raw_url:
        print(
            "Defina DATABASE_URL, QDI_POSTGRES_TEST_URL ou passe a DSN como argumento.",
            file=sys.stderr,
        )
        return 1

    dsn = _dsn_normalizado(raw_url)

    try:
        tabelas = asyncio.run(_executar(dsn))
    except Exception as exc:
        print(f"Falha de conexão ou execução: {exc}", file=sys.stderr)
        return 1

    print("Relatório RLS — schema public (PostgreSQL)")
    print(f"Total de tabelas com RLS activo: {len(tabelas)}")
    if tabelas:
        print("")
        for nome in tabelas:
            print(f"  - {nome}")
    else:
        print("")
        print("  (nenhuma tabela base com relrowsecurity=true encontrada)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
