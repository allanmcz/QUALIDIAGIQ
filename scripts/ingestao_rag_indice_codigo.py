#!/usr/bin/env python3
"""
Fase G — gera índice JSON de docstrings/comentários em ``src/`` e ADRs para RAG Ollama local.

Saída default: ``.cache/qdi_rag_codigo_chunks.json`` (referenciado por ``QDI_RAG_CODIGO_INDEX_PATH``).

Uso:
  PYTHONPATH=. python scripts/ingestao_rag_indice_codigo.py
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".cache" / "qdi_rag_codigo_chunks.json"
SRC = ROOT / "src"
ADR = ROOT / ".github" / "adr"


def _extrair_docstring_modulo(path: Path) -> str | None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return None
    doc = ast.get_docstring(tree)
    return doc.strip() if doc else None


def _chunks_de_path(path: Path, *, fonte: str) -> list[dict[str, str]]:
    rel = str(path.relative_to(ROOT))
    texto = path.read_text(encoding="utf-8", errors="replace")
    saida: list[dict[str, str]] = []
    if path.suffix == ".py":
        doc = _extrair_docstring_modulo(path)
        if doc and len(doc) > 40:
            saida.append({"fonte": fonte, "artigo": rel, "texto": doc[:2000]})
        for match in re.finditer(
            r'"""(.*?)"""',
            texto,
            flags=re.DOTALL,
        ):
            bloco = match.group(1).strip()
            if len(bloco) > 80:
                saida.append(
                    {
                        "fonte": fonte,
                        "artigo": f"{rel}#doc",
                        "texto": bloco[:1500],
                    }
                )
    elif path.suffix == ".md":
        if len(texto.strip()) > 80:
            saida.append({"fonte": fonte, "artigo": rel, "texto": texto[:2500]})
    return saida


def main() -> None:
    registos: list[dict[str, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        if "test" in path.parts or path.name.startswith("__"):
            continue
        registos.extend(_chunks_de_path(path, fonte="CODIGO_SRC"))
    if ADR.is_dir():
        for path in sorted(ADR.glob("ADR-*.md")):
            registos.extend(_chunks_de_path(path, fonte="ADR"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(registos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gravado {len(registos)} trechos em {OUT}")


if __name__ == "__main__":
    main()
