#!/usr/bin/env python3
"""
Verifica no Postgres alvo se o schema mínimo do MVP está presente (migrações até 0012 + RLS).

Uso (uma das opções):
  DATABASE_URL=postgresql://user:pass@host:5432/db python scripts/verify_mvp_schema.py
  QDI_POSTGRES_TEST_URL=postgresql://... python scripts/verify_mvp_schema.py
  python scripts/verify_mvp_schema.py postgresql://user:pass@host:5432/db

Aceita URL com prefixo ``postgresql+asyncpg://`` (normaliza para asyncpg).

Saída: mensagens em PT-BR; código de saída 0 = OK, 1 = falha.

Camada: ferramenta de operação (fora da Clean Architecture — apenas diagnóstico de infra).
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg


def _dsn_normalizado(raw: str) -> str:
    return raw.strip().replace("postgresql+asyncpg://", "postgresql://", 1)


async def _verificar(conn_dsn: str) -> list[str]:
    erros: list[str] = []
    conn = await asyncpg.connect(conn_dsn, timeout=10)

    try:
        aceite = await conn.fetchval("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'diagnosticos'
              AND column_name = 'aceite_termos_privacidade_em'
            """)
        if aceite != 1:
            erros.append(
                "Coluna public.diagnosticos.aceite_termos_privacidade_em ausente "
                "(aplique migração 0012 ou equivalente)."
            )

        m12 = await conn.fetchval("""
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'diagnosticos'
              AND column_name = 'checklist_m12_estado'
            """)
        if m12 != 1:
            erros.append("Coluna public.diagnosticos.checklist_m12_estado ausente (migração 0011).")

        rls = await conn.fetchval("""
            SELECT c.relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'diagnosticos'
            """)
        if rls is not True:
            erros.append(
                "RLS não habilitada em public.diagnosticos (ver migração 0003_rls_policies.sql)."
            )

        n_pol = await conn.fetchval("""
            SELECT count(*)::int
            FROM pg_policies
            WHERE schemaname = 'public' AND tablename = 'diagnosticos'
            """)
        if (n_pol or 0) < 4:
            erros.append(
                f"Esperadas políticas RLS em diagnosticos (>=4); encontradas: {n_pol or 0}."
            )

        fn = await conn.fetchval("""
            SELECT 1
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = 'public' AND p.proname = 'qdi_jwt_tenant_id'
            """)
        if fn != 1:
            erros.append("Função public.qdi_jwt_tenant_id ausente (necessária para políticas RLS).")
    finally:
        await conn.close()

    return erros


def main() -> int:
    raw_url = (
        (sys.argv[1] if len(sys.argv) > 1 else None)
        or os.environ.get("DATABASE_URL")
        or os.environ.get("QDI_POSTGRES_TEST_URL")
    )
    if not raw_url:
        print(
            "Defina DATABASE_URL, QDI_POSTGRES_TEST_URL ou passe a DSN como argumento.",
            file=sys.stderr,
        )
        return 1

    dsn = _dsn_normalizado(raw_url)

    try:
        erros = asyncio.run(_verificar(dsn))
    except Exception as exc:
        print(f"Falha de conexão ou execução: {exc}", file=sys.stderr)
        return 1

    if erros:
        print("Verificação MVP schema: FALHA", file=sys.stderr)
        for e in erros:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("Verificação MVP schema: OK (0012 + M12 + RLS + qdi_jwt_tenant_id).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
