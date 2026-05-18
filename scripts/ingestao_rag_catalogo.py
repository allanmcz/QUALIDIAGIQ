#!/usr/bin/env python3
"""
Ingestão RAG — corpus do ``catalogo_fontes.yml`` → ``qdi_rag.documento_normativo``.

Suporta Markdown direto e ficheiros extraídos (``dominio_fiscal/extraido/FONTE-xxx.md``).
Para PDF/XLSX: executar antes ``scripts/extrair_fontes_catalogo_rag.py``.

Uso:
  PYTHONPATH=. python scripts/ingestao_rag_catalogo.py --dry-run
  OPENAI_API_KEY=... DATABASE_URL=... PYTHONPATH=. python scripts/ingestao_rag_catalogo.py
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]

from src.infrastructure.adapters.base_normativa_pgvector import (  # noqa: E402
    _embedding_openai,
    _vetor_para_sql_literal,
)
from src.infrastructure.rag.catalogo_fontes_index import (  # noqa: E402
    caminho_ficheiro_ingestivel,
    carregar_entradas_catalogo,
)


def _chunk_text(text: str, max_chars: int = 1400, overlap: int = 120) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    if len(t) <= max_chars:
        return [t]
    out: list[str] = []
    start = 0
    while start < len(t):
        end = min(start + max_chars, len(t))
        piece = t[start:end].strip()
        if piece:
            out.append(piece)
        if end >= len(t):
            break
        start = max(0, end - overlap)
    return out


async def _ingest_path(
    conn: asyncpg.Connection | None,
    *,
    fonte_id: str,
    caminho: Path,
    caminho_relativo: str,
    api_key: str,
    model: str,
    vigencia: date,
    dry_run: bool,
) -> int:
    if not caminho.is_file():
        print(f"AVISO: ausente {caminho}", file=sys.stderr)
        return 0
    raw = caminho.read_text(encoding="utf-8", errors="replace")
    n = 0
    for chunk in _chunk_text(raw):
        if dry_run:
            n += 1
            continue
        assert conn is not None
        vec = await _embedding_openai(chunk, api_key=api_key, model=model)
        literal = _vetor_para_sql_literal(vec)
        await conn.execute(
            """
            INSERT INTO qdi_rag.documento_normativo (fonte, artigo, texto, embedding, vigencia_inicio)
            VALUES ($1, $2, $3, $4::vector, $5)
            """,
            fonte_id,
            caminho_relativo,
            chunk,
            literal,
            vigencia,
        )
        n += 1
    return n


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingestão RAG a partir do catálogo de fontes.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--somente-piloto", action="store_true", default=True)
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL", "").strip()
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()
    if not args.dry_run and (not dsn or not api_key):
        print("DATABASE_URL e OPENAI_API_KEY obrigatórios.", file=sys.stderr)
        sys.exit(1)

    vigencia = date(2025, 1, 1)
    conn: asyncpg.Connection | None = None
    if not args.dry_run:
        conn = await asyncpg.connect(dsn.replace("postgresql+asyncpg://", "postgresql://", 1))

    total = 0
    try:
        for ent in carregar_entradas_catalogo():
            if args.somente_piloto and not ent.piloto:
                continue
            path = caminho_ficheiro_ingestivel(ent)
            if path is None:
                print(
                    f"SKIP: sem texto legível {ent.id} ({ent.caminho}) — extrair PDF/XLSX?",
                    file=sys.stderr,
                )
                continue
            rel = str(path.relative_to(ROOT))
            n = await _ingest_path(
                conn,
                fonte_id=ent.id,
                caminho=path,
                caminho_relativo=rel,
                api_key=api_key,
                model=model,
                vigencia=vigencia,
                dry_run=args.dry_run,
            )
            total += n
            print(f"{ent.id}: {n} chunks")
    finally:
        if conn is not None:
            await conn.close()

    print(f"Total chunks: {total}" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    asyncio.run(main())
