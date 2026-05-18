#!/usr/bin/env python3
"""
Fase D IA_DIAG_V2 — RAG piloto local (Markdown QDI + embeddings Ollama).

Sem pgvector: similaridade coseno em memoria sobre chunks de docs/refs piloto.
Gate DP-006: exige fonte ou declara base insuficiente.

Uso:
  PYTHONPATH=. python scripts/ia_diag_v2_fase_d_rag_piloto.py
"""

from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "dominio_fiscal" / "catalogo_fontes.yml"
EMBED_MODEL = "mxbai-embed-large:latest"
EMBED_URL = "http://127.0.0.1:11434/api/embed"
THRESHOLD = 0.45

# Piloto classe B — ja em Markdown (Fase D sem extrair PDF ainda)
MD_PILOTO = (
    "docs/refs/01_PRD_BASE.md",
    "docs/refs/02_MOSCOW_FEATURES.md",
    "docs/refs/04_METODOLOGIA.md",
    "docs/refs/05_QUESTIONARIO_v1.md",
)

QUERIES = [
    "Qual o escopo do MVP do QualiDiagIQ e o que fica fora?",
    "Como o score 0-100 e calculado no diagnostico?",
    "O que e cClassTrib na reforma tributaria?",
    "Posso apurar CBS continuamente no QDI?",
]


def _chunk_md(text: str, fonte_id: str, caminho: str, *, size: int = 800) -> list[dict[str, str]]:
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[dict[str, str]] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 > size and buf:
            chunks.append({"fonte_id": fonte_id, "caminho": caminho, "texto": buf.strip()})
            buf = p
        else:
            buf = f"{buf}\n\n{p}".strip() if buf else p
    if buf:
        chunks.append({"fonte_id": fonte_id, "caminho": caminho, "texto": buf.strip()})
    return chunks


def _embed(text: str) -> list[float]:
    body = json.dumps({"model": EMBED_MODEL, "input": text[:2000]}).encode()
    req = urllib.request.Request(
        EMBED_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
    embs = data.get("embeddings") or []
    if embs:
        return list(embs[0])
    return list(data["embedding"])


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def main() -> None:
    import yaml

    cat = yaml.safe_load(CATALOGO.read_text(encoding="utf-8"))
    id_por_caminho = {f["caminho"]: f["id"] for f in cat["fontes"] if f.get("piloto")}

    chunks: list[dict[str, object]] = []
    for rel in MD_PILOTO:
        path = ROOT / rel
        if not path.is_file():
            print(f"AVISO: ausente {rel}", file=sys.stderr)
            continue
        fid = id_por_caminho.get(rel, "FONTE-?")
        for ch in _chunk_md(path.read_text(encoding="utf-8", errors="replace"), fid, rel):
            chunks.append(ch)

    print(f"Chunks: {len(chunks)}", file=sys.stderr)
    for i, ch in enumerate(chunks):
        texto = str(ch["texto"]).strip()
        if len(texto) < 20:
            ch["embedding"] = []
            continue
        try:
            ch["embedding"] = _embed(texto)
        except Exception as exc:
            print(f"AVISO chunk {i} embed falhou: {exc}", file=sys.stderr)
            ch["embedding"] = []
        if (i + 1) % 10 == 0:
            print(f"  embed {i + 1}/{len(chunks)}", file=sys.stderr)

    relatorio: list[dict[str, object]] = []
    for q in QUERIES:
        q_emb = _embed(q)
        scored = sorted(
            (
                {
                    "score": _cos(q_emb, emb),
                    "fonte_id": c["fonte_id"],
                    "caminho": c["caminho"],
                    "trecho": str(c["texto"])[:280].replace("\n", " "),
                }
                for c in chunks
                if (emb := list(c.get("embedding") or []))  # type: ignore[arg-type]
            ),
            key=lambda x: float(x["score"]),
            reverse=True,
        )
        top = scored[:3]
        melhor = float(top[0]["score"]) if top else 0.0
        status = "com_fonte" if melhor >= THRESHOLD else "base_insuficiente"
        relatorio.append({"pergunta": q, "status": status, "melhor_score": melhor, "top": top})

    out = ROOT / "_DEVELOPER/IA_DIAG_V2/reports/fase_d_rag_piloto.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {out}")
    for row in relatorio:
        print(f"\nQ: {row['pergunta']}")
        print(f"   {row['status']} (score={row['melhor_score']:.3f})")
        for t in row["top"][:2]:  # type: ignore[index]
            print(f"   - {t['fonte_id']} {t['score']:.3f} {t['caminho']}")


if __name__ == "__main__":
    main()
