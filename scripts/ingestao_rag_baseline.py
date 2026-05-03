#!/usr/bin/env python3
"""
Ingestão baseline RAG-light: arquivos ``scripts/normativos_baseline/*.txt`` → embeddings OpenAI → ``qdi_rag.documento_normativo``.

Requer migração ``0020_pgvector_rag_light.sql``, imagem Postgres com extensão ``vector``, ``DATABASE_URL`` e ``OPENAI_API_KEY``.

Uso:
  OPENAI_API_KEY=... DATABASE_URL=postgresql://... python scripts/ingestao_rag_baseline.py
  python scripts/ingestao_rag_baseline.py --dry-run

Camada: operação (fora da Clean Architecture).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import date
from pathlib import Path

import asyncpg

from src.infrastructure.adapters.base_normativa_pgvector import (
    _embedding_openai,
    _vetor_para_sql_literal,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _fonte_artigo(path: Path) -> tuple[str, str | None]:
    stem = path.stem.lower()
    if "lc214" in stem:
        return "LC 214/2025", "baseline"
    if "ec132" in stem:
        return "EC 132/2023", "baseline"
    if "17301" in stem or "abnt" in stem:
        return "ABNT NBR 17301:2026", "baseline"
    return path.stem, None


def _chunk_text(text: str, max_chars: int = 1400, overlap: int = 120) -> list[str]:
    """Segmenta texto em blocos com sobreposição leve (RF dividido)."""
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


async def _ingest_file(
    conn: asyncpg.Connection | None,
    path: Path,
    *,
    api_key: str,
    model: str,
    vigencia: date,
    dry_run: bool,
) -> int:
    raw = path.read_text(encoding="utf-8")
    chunks = _chunk_text(raw)
    fonte, artigo = _fonte_artigo(path)
    n = 0
    for chunk in chunks:
        if dry_run:
            print(f"[dry-run] {path.name} #{n + 1} chars={len(chunk)} fonte={fonte}")
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
            fonte,
            artigo,
            chunk,
            literal,
            vigencia,
        )
        n += 1
    return n


async def _async_main(args: argparse.Namespace) -> int:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    raw_dsn = (
        (args.dsn or "").strip()
        or os.environ.get("DATABASE_URL", "").strip()
        or os.environ.get("QDI_POSTGRES_TEST_URL", "").strip()
    )
    dsn = raw_dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    root = Path(args.normativos_dir).resolve()
    files = sorted(root.glob("*.txt"))
    if not files:
        print(f"Nenhum .txt encontrado em {root}", file=sys.stderr)
        return 1

    if not args.dry_run:
        if not api_key:
            print("Defina OPENAI_API_KEY.", file=sys.stderr)
            return 1
        if not dsn:
            print("Defina DATABASE_URL ou passe --dsn.", file=sys.stderr)
            return 1

    vigencia = date.fromisoformat(args.vigencia_inicio)
    conn: asyncpg.Connection | None = None
    if not args.dry_run:
        conn = await asyncpg.connect(dsn, timeout=15)

    total = 0
    try:
        for f in files:
            total += await _ingest_file(
                conn,
                f,
                api_key=api_key,
                model=args.embedding_model,
                vigencia=vigencia,
                dry_run=args.dry_run,
            )
    finally:
        if conn is not None:
            await conn.close()

    modo = "dry-run" if args.dry_run else "commit"
    print(f"Ingestão baseline ({modo}): {total} chunk(s) de {len(files)} arquivo(s).")
    return 0


def main() -> int:
    default_dir = _repo_root() / "scripts" / "normativos_baseline"
    parser = argparse.ArgumentParser(description="Ingestão RAG baseline (OpenAI + pgvector).")
    parser.add_argument(
        "--normativos-dir",
        default=str(default_dir),
        help="Pasta com arquivos .txt (default: scripts/normativos_baseline).",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        help="Modelo OpenAI embeddings (default: text-embedding-3-small).",
    )
    parser.add_argument(
        "--vigencia-inicio",
        default=os.environ.get("QDI_RAG_VIGENCIA_INICIO", "2026-01-01"),
        help="Data vigencia_inicio (ISO).",
    )
    parser.add_argument("--dsn", default="", help="Postgres DSN (senão DATABASE_URL).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Lista chunks sem chamar OpenAI nem gravar no banco.",
    )
    args = parser.parse_args()
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
