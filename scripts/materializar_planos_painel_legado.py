#!/usr/bin/env python3
"""
Backfill D1-C — materializa plano/matriz/cronograma para diagnósticos finalizados sem linhas em ``diagnostico_plano_acao``.

Uso:
  DATABASE_URL=postgresql://... python scripts/materializar_planos_painel_legado.py
  python scripts/materializar_planos_painel_legado.py postgresql://...

Saída: contagem de processados / ignorados / erros (stderr em caso de traceback por ID).
"""

from __future__ import annotations

import asyncio
import sys
from uuid import UUID

from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)


def _dsn(argv: list[str]) -> str:
    for a in argv[1:]:
        if a.startswith("postgresql"):
            return a.strip()
    raise SystemExit("Passe DATABASE_URL ou o DSN como primeiro argumento posicional.")


async def _main(dsn: str) -> None:
    repo = PostgresDiagnosticoRepository(dsn_sync=dsn)
    # Lista simples: todos os tenants (operador com BYPASSRLS ou superuser). Em produção restrinja por tenant.
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.id, d.tenant_id
                FROM diagnosticos d
                WHERE d.status = 'finalizado'
                  AND NOT EXISTS (
                    SELECT 1 FROM diagnostico_plano_acao p
                    WHERE p.diagnostico_id = d.id AND p.tenant_id = d.tenant_id
                  )
                ORDER BY d.finalizado_em NULLS LAST, d.criado_em
                """)
            rows = cur.fetchall()
    finally:
        conn.close()

    ok = skip = err = 0
    for row in rows:
        did = UUID(str(row["id"]))
        tid = UUID(str(row["tenant_id"]))
        try:
            out = await repo.materializar_plano_painel_idempotente_backfill(did, tid)
            if out is None:
                skip += 1
            else:
                ok += 1
        except Exception as e:
            err += 1
            print(f"ERRO {did} tenant={tid}: {e}", file=sys.stderr)
    print(f"materializados={ok} ignorados={skip} erros={err} candidatos={len(rows)}")


if __name__ == "__main__":
    dsn = _dsn(sys.argv)
    asyncio.run(_main(dsn))
