#!/usr/bin/env python3
"""
Backfill operacional por empresa (CNPJ ou razão social) — plano materializado + respostas (se houver fonte).

Uso:
  DATABASE_URL=postgresql://postgres:postgres@localhost:60322/postgres \\
    python scripts/backfill_materializacao_empresa.py --cnpj 29261608000151

  python scripts/backfill_materializacao_empresa.py postgresql://... --razao "OLIVEIRA & SILVA"

Requer acesso ao Postgres (BYPASSRLS ou superuser em dev).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor

from src.application.services.diagnostico_payload_respostas import (
    entradas_resposta_de_payload_dict,
)
from src.application.services.diagnostico_resposta_materializacao import (
    derivar_respostas_e_linhas,
)
from src.infrastructure.repositories.postgres_backfill_respostas_questionario_sync import (
    buscar_payload_rascunho_para_backfill_sync,
    persistir_linhas_backfill_sync,
)
from src.infrastructure.repositories.postgres_diagnostico_resposta_sync import (
    respostas_questionario_existem_sync,
)
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)


def _dsn_from_args(argv: list[str]) -> str:
    import os

    for a in argv:
        if a.startswith("postgresql"):
            return a.strip()
    env = os.environ.get("DATABASE_URL", "").strip()
    if env:
        return env
    raise SystemExit("Defina DATABASE_URL ou passe o DSN postgresql:// como argumento.")


def _only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _listar_diagnosticos_finalizados(
    dsn: str,
    *,
    cnpj14: str | None,
    razao_like: str | None,
    tenant_id: UUID | None,
) -> list[dict[str, Any]]:
    clauses = ["d.status = 'finalizado'"]
    params: list[Any] = []
    if tenant_id is not None:
        clauses.append("d.tenant_id = %s")
        params.append(str(tenant_id))
    if cnpj14:
        clauses.append("d.empresa_cnpj = %s")
        params.append(cnpj14)
    if razao_like:
        clauses.append("upper(d.empresa_razao_social) LIKE %s")
        params.append(f"%{razao_like.upper()}%")
    if not cnpj14 and not razao_like:
        raise SystemExit("Informe --cnpj ou --razao.")

    sql = f"""
        SELECT d.id, d.tenant_id, d.empresa_cnpj, d.empresa_razao_social, d.finalizado_em,
               EXISTS (
                 SELECT 1 FROM diagnostico_plano_acao p
                 WHERE p.diagnostico_id = d.id AND p.tenant_id = d.tenant_id
               ) AS tem_plano,
               EXISTS (
                 SELECT 1 FROM diagnostico_resposta_questionario drq
                 WHERE drq.diagnostico_id = d.id
               ) AS tem_respostas
        FROM diagnosticos d
        WHERE {" AND ".join(clauses)}
        ORDER BY d.finalizado_em DESC NULLS LAST, d.criado_em DESC
    """
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def _vincular_cnpj_consultas(dsn: str, diagnostico_id: UUID, tenant_id: UUID, cnpj14: str) -> int:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE cnpj_consultas
                SET diagnostico_id = %s
                WHERE tenant_id = %s
                  AND cnpj = %s
                  AND diagnostico_id IS NULL
                """,
                (str(diagnostico_id), str(tenant_id), cnpj14),
            )
            n = cur.rowcount
        conn.commit()
        return n
    finally:
        conn.close()


def _inventario(dsn: str, diagnostico_id: UUID) -> dict[str, int]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                  (SELECT count(*) FROM diagnostico_plano_acao WHERE diagnostico_id = %s) AS plano_acao,
                  (SELECT count(*) FROM diagnostico_plano_matriz WHERE diagnostico_id = %s) AS plano_matriz,
                  (SELECT count(*) FROM diagnostico_plano_cronograma WHERE diagnostico_id = %s) AS plano_cronograma,
                  (SELECT count(*) FROM diagnostico_resposta_questionario WHERE diagnostico_id = %s) AS respostas,
                  (SELECT count(*) FROM diagnostico_retificacao WHERE diagnostico_original_id = %s) AS retificacao
                """,
                (str(diagnostico_id),) * 5,
            )
            row = cur.fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Backfill materialização por empresa (QDI).")
    parser.add_argument("dsn_posicional", nargs="?", help="DSN postgresql:// (opcional se DATABASE_URL)")
    parser.add_argument("--cnpj", help="CNPJ 14 dígitos")
    parser.add_argument("--razao", help="Trecho da razão social (ILIKE)")
    parser.add_argument("--tenant-id", help="UUID do tenant (opcional)")
    parser.add_argument(
        "--janela-horas-rascunho",
        type=int,
        default=168,
        help="Janela para casar rascunho self-service (padrão 168h).",
    )
    args = parser.parse_args()

    argv_dsn = [a for a in sys.argv[1:] if a.startswith("postgresql")]
    dsn = argv_dsn[0] if argv_dsn else _dsn_from_args(sys.argv)

    cnpj14 = _only_digits(args.cnpj) if args.cnpj else None
    if cnpj14 and len(cnpj14) != 14:
        raise SystemExit("CNPJ deve ter 14 dígitos.")
    tenant_id = UUID(args.tenant_id) if args.tenant_id else None

    rows = _listar_diagnosticos_finalizados(
        dsn, cnpj14=cnpj14, razao_like=args.razao, tenant_id=tenant_id
    )
    if not rows:
        print("Nenhum diagnóstico finalizado encontrado para o filtro.")
        return

    repo = PostgresDiagnosticoRepository(dsn_sync=dsn)
    relatorio: list[dict[str, Any]] = []

    for row in rows:
        did = UUID(str(row["id"]))
        tid = UUID(str(row["tenant_id"]))
        cnpj = str(row["empresa_cnpj"])
        item: dict[str, Any] = {
            "diagnostico_id": str(did),
            "razao_social": row["empresa_razao_social"],
            "cnpj": cnpj,
            "plano_antes": bool(row["tem_plano"]),
            "respostas_antes": bool(row["tem_respostas"]),
        }

        if not row["tem_plano"]:
            try:
                out = await repo.materializar_plano_painel_idempotente_backfill(did, tid)
                item["plano"] = "materializado" if out else "ignorado_sem_score"
            except Exception as exc:
                item["plano"] = f"erro: {exc}"
        else:
            item["plano"] = "ja_existia"

        if not row["tem_respostas"]:
            if respostas_questionario_existem_sync(dsn, did, tid):
                item["respostas"] = "ja_existia"
            else:
                payload = buscar_payload_rascunho_para_backfill_sync(
                    dsn, did, tid, janela_horas=args.janela_horas_rascunho
                )
                if payload is None:
                    item["respostas"] = "sem_fonte"
                    item["respostas_motivo"] = (
                        "Sem rascunho self-service, idempotency ou payload recuperável."
                    )
                else:
                    try:
                        entradas = entradas_resposta_de_payload_dict(payload)
                        _, linhas = derivar_respostas_e_linhas(did, entradas)
                        if not linhas:
                            item["respostas"] = "sem_fonte"
                            item["respostas_motivo"] = "Rascunho sem lista respostas."
                        else:
                            ok = persistir_linhas_backfill_sync(dsn, did, tid, linhas)
                            item["respostas"] = (
                                "preenchido" if ok else "ja_existia_concorrente"
                            )
                            item["total_respostas"] = len(linhas)
                    except ValueError as ve:
                        item["respostas"] = f"erro_payload: {ve}"
        else:
            item["respostas"] = "ja_existia"

        n_vinc = _vincular_cnpj_consultas(dsn, did, tid, cnpj)
        item["cnpj_consultas_vinculadas"] = n_vinc
        item["inventario"] = _inventario(dsn, did)
        relatorio.append(item)

    print(json.dumps({"processados": len(relatorio), "itens": relatorio}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(_main())
