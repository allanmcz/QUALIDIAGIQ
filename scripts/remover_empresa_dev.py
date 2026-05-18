#!/usr/bin/env python3
"""
Remove empresa (CNPJ) do ambiente de desenvolvimento — inclui diagnósticos **finalizados**.

**Não usar em produção** — viola evidência WORM (ADR-012). Em produção use fluxo LGPD.

Uso:
  PYTHONPATH=. DATABASE_URL=postgresql://postgres:postgres@localhost:60322/postgres \\
    python scripts/remover_empresa_dev.py --cnpj 29261608000151

  python scripts/remover_empresa_dev.py postgresql://... --cnpj ... --tenant-id UUID
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor


def _dsn() -> str:
    for a in sys.argv[1:]:
        if a.startswith("postgresql"):
            return a.strip()
    env = os.environ.get("DATABASE_URL", "").strip()
    if env:
        return env
    raise SystemExit("Defina DATABASE_URL ou passe DSN postgresql://.")


def _only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


# Ordem: dependentes do plano antes das linhas de ação; retificação por original_id.
_TABELAS_FILHAS: tuple[tuple[str, str], ...] = (
    ("diagnostico_plano_subtarefa", "diagnostico_id"),
    ("diagnostico_plano_acao_comentario", "diagnostico_id"),
    ("diagnostico_plano_acao_estado", "diagnostico_id"),
    ("diagnostico_plano_acao", "diagnostico_id"),
    ("diagnostico_plano_matriz", "diagnostico_id"),
    ("diagnostico_plano_cronograma", "diagnostico_id"),
    ("diagnostico_resposta_questionario", "diagnostico_id"),
    ("diagnostico_retificacao", "diagnostico_original_id"),
    ("diagnostico_explicacao_score_llm_historico", "diagnostico_id"),
    ("diagnostico_leitura_publica_self_service", "diagnostico_id"),
    ("diagnostico_empresa_campo_historico", "diagnostico_id"),
    ("lgpd_anonimizacao_log", "diagnostico_id"),
    ("diagnostico_mutacao_audit", "diagnostico_id"),
)


def _apagar_filhos_diagnosticos(cur: Any, ids: list[str]) -> dict[str, int]:
    """Remove linhas filhas com triggers append-only desligados (somente DEV)."""
    cur.execute("SET LOCAL session_replication_role = replica")
    contagens: dict[str, int] = {}
    for tabela, coluna in _TABELAS_FILHAS:
        cur.execute(
            f"DELETE FROM {tabela} WHERE {coluna} = ANY(%s::uuid[])",
            (ids,),
        )
        if cur.rowcount > 0:
            contagens[tabela] = cur.rowcount
    cur.execute("SET LOCAL session_replication_role = DEFAULT")
    return contagens


def _remover(
    dsn: str,
    cnpj14: str,
    tenant_id: UUID | None,
    *,
    mock_storage_dir: Path | None,
) -> dict[str, Any]:
    conn = psycopg2.connect(dsn)
    relatorio: dict[str, Any] = {"cnpj": cnpj14, "tenant_id": str(tenant_id) if tenant_id else None}
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            params: list[Any] = [cnpj14]
            filtro_tenant = ""
            if tenant_id is not None:
                filtro_tenant = " AND tenant_id = %s"
                params.append(str(tenant_id))

            cur.execute(
                f"""
                SELECT id, tenant_id, relatorio_pdf_url
                FROM diagnosticos
                WHERE empresa_cnpj = %s{filtro_tenant}
                """,
                params,
            )
            diagnosticos = [dict(r) for r in cur.fetchall()]
            relatorio["diagnosticos_encontrados"] = len(diagnosticos)

            if not diagnosticos:
                conn.rollback()
                relatorio["status"] = "nada_a_remover"
                return relatorio

            ids = [str(d["id"]) for d in diagnosticos]
            tenants = list({str(d["tenant_id"]) for d in diagnosticos})

            relatorio["filhos_removidos"] = _apagar_filhos_diagnosticos(cur, ids)
            cur.execute(
                "DELETE FROM diagnosticos WHERE id = ANY(%s::uuid[])",
                (ids,),
            )
            relatorio["diagnosticos_removidos"] = cur.rowcount

            cur.execute(
                f"""
                DELETE FROM cnpj_consultas
                WHERE cnpj = %s{filtro_tenant}
                """,
                params,
            )
            relatorio["cnpj_consultas_removidas"] = cur.rowcount

            for tid in tenants:
                cur.execute(
                    """
                    DELETE FROM empresa_painel_arquivo
                    WHERE tenant_id = %s AND empresa_cnpj = %s
                    """,
                    (tid, cnpj14),
                )
            relatorio["empresa_painel_arquivo_removidas"] = cur.rowcount

        conn.commit()
        relatorio["status"] = "ok"
        relatorio["diagnostico_ids"] = ids

        if mock_storage_dir and mock_storage_dir.is_dir():
            pdfs_removidos = 0
            for d in diagnosticos:
                tid = str(d["tenant_id"])
                did = str(d["id"])
                for nome in (f"{did}.pdf",):
                    path = mock_storage_dir / tid / nome
                    if path.is_file():
                        path.unlink()
                        pdfs_removidos += 1
            relatorio["pdfs_mock_storage_removidos"] = pdfs_removidos

        return relatorio
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove empresa do Postgres (somente DEV).")
    parser.add_argument("--cnpj", required=True, help="CNPJ 14 dígitos")
    parser.add_argument("--tenant-id", help="UUID do tenant (recomendado)")
    parser.add_argument(
        "--mock-storage-dir",
        default=os.environ.get("QDI_MOCK_PDF_STORAGE_DIR", "/tmp/qdi-mock-pdf"),
        help="Pasta do fallback /mock-storage (opcional)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Confirma remoção sem prompt interativo",
    )
    args = parser.parse_args()

    cnpj14 = _only_digits(args.cnpj)
    if len(cnpj14) != 14:
        raise SystemExit("CNPJ deve ter 14 dígitos.")

    if not args.yes:
        print(
            f"AVISO: removerá TODOS os diagnósticos (incl. finalizados) do CNPJ {cnpj14} "
            f"no ambiente apontado por DATABASE_URL.",
            file=sys.stderr,
        )
        print("Repita com --yes para confirmar.", file=sys.stderr)
        raise SystemExit(1)

    tenant_id = UUID(args.tenant_id) if args.tenant_id else None
    mock_dir = Path(args.mock_storage_dir) if args.mock_storage_dir else None

    dsn = _dsn()
    out = _remover(dsn, cnpj14, tenant_id, mock_storage_dir=mock_dir)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
