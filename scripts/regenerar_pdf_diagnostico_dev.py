#!/usr/bin/env python3
"""
Regenera o PDF de um diagnóstico finalizado e repõe o spool mock (/mock-storage).

Uso (Compose — Postgres na porta 60322):
  DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:60322/postgres \\
    QDI_PUBLIC_API_BASE_URL=http://127.0.0.1:60000 \\
    python scripts/regenerar_pdf_diagnostico_dev.py <diagnostico_id>

Dentro do container API (volume do spool já montado):
  docker compose exec api python scripts/regenerar_pdf_diagnostico_dev.py <diagnostico_id>
"""

from __future__ import annotations

import asyncio
import os
import sys
from uuid import UUID

import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client

from src.application.services.explicacao_score_publica import (
    texto_explicacao_score_para_leitura_publica,
)
from src.domain.entities.diagnostico import StatusDiagnostico
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter
from src.infrastructure.config.settings import get_settings
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
    _row_dict_para_entity,
)


def _normalizar_dsn_psycopg2(raw: str) -> str:
    """``DATABASE_URL`` do Compose pode vir como ``postgresql+asyncpg://`` — psycopg2 exige ``postgresql://``."""
    s = raw.strip()
    if s.startswith("postgresql+asyncpg://"):
        return "postgresql://" + s.removeprefix("postgresql+asyncpg://")
    return s


def _dsn(argv: list[str]) -> str:
    for a in argv[2:]:
        if a.startswith("postgresql"):
            return _normalizar_dsn_psycopg2(a)
    env = os.environ.get("DATABASE_URL", "").strip()
    if env:
        return _normalizar_dsn_psycopg2(env)
    raise SystemExit(
        "Defina DATABASE_URL ou passe o DSN postgres como 2.º argumento.\n"
        "Ex.: postgresql://postgres:postgres@127.0.0.1:60322/postgres"
    )


def _carregar_diagnostico(dsn: str, diagnostico_id: UUID) -> tuple[object, UUID]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT *
                FROM diagnosticos
                WHERE id = %s
                LIMIT 1
                """,
                (str(diagnostico_id),),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    if row is None:
        raise SystemExit(f"Diagnóstico não encontrado: {diagnostico_id}")
    diag = _row_dict_para_entity(dict(row))
    if diag.status != StatusDiagnostico.FINALIZADO:
        raise SystemExit(
            f"Diagnóstico {diagnostico_id} não está finalizado (status={diag.status.value})."
        )
    if diag.score_completo_snapshot is None:
        raise SystemExit("Sem score_completo na BD — não é possível renderizar o PDF.")
    return diag, diag.tenant_id


async def _regenerar(dsn: str, diagnostico_id: UUID) -> str:
    diag, tenant_id = _carregar_diagnostico(dsn, diagnostico_id)
    score = diag.score_completo_snapshot
    assert score is not None

    expl = texto_explicacao_score_para_leitura_publica(getattr(diag, "explicacao_score_llm", None))
    pdf_gen = WeasyPrintPdfGenerator()
    pdf_bytes = await pdf_gen.gerar_pdf_diagnostico(
        diag,
        score,
        recomendacao_ia=None,
        explicacao_score_llm_texto=expl,
    )

    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_key)
    storage = SupabaseStorageAdapter(client)
    url = await storage.upload_pdf(tenant_id, diagnostico_id, pdf_bytes)

    repo = PostgresDiagnosticoRepository(dsn_sync=dsn)
    atualizado = await repo.atualizar_relatorio_pdf_com_versao(
        diagnostico_id,
        tenant_id,
        url,
        versao_esperada=diag.versao_otimista,
    )
    if atualizado is None:
        raise RuntimeError("Conflito de versão otimista — repita após refresh do GET.")

    return url


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Uso: python scripts/regenerar_pdf_diagnostico_dev.py <diagnostico_id>", file=sys.stderr
        )
        return 1
    try:
        did = UUID(sys.argv[1].strip())
    except ValueError:
        print("diagnostico_id inválido (esperado UUID).", file=sys.stderr)
        return 1
    dsn = _dsn(sys.argv)
    try:
        url = asyncio.run(_regenerar(dsn, did))
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    print(f"PDF regenerado.\n  URL: {url}\n  Abra no painel ou: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
