#!/usr/bin/env python3
"""
Auditoria 37x35 — pilares ABNT no catálogo vs texto fixo em docs/refs/05_QUESTIONARIO_v1.md.

Objetivo: garantir que perguntas **Q-ABNT-*** tenham ``pilar_abnt`` alinhado aos eixos/capítulos
descritos na secção 8 do PRD do questionário (sem inferência normativa nova).

Uso (raiz do repo):
    PYTHONPATH=. python scripts/auditoria_pilar_abnt_catalogo.py

Código de saída: 0 = OK, 1 = divergência.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "src/infrastructure/questionario/data/perguntas_mvp.json"
MD_PATH = ROOT / "docs/refs/05_QUESTIONARIO_v1.md"

# Texto após o código da pergunta no Markdown — captura título do eixo até o fim da linha.
MD_ABNT_HEADER = re.compile(
    r"^###\s+(Q-ABNT-\d{3})\s+—\s+(.+)$",
    re.MULTILINE,
)


def _esperado_md_por_codigo() -> dict[str, str]:
    texto = MD_PATH.read_text(encoding="utf-8")
    bloco_inicio = texto.find("## 8. Bloco 5 — Compliance ABNT")
    if bloco_inicio < 0:
        raise RuntimeError("Secção 8 (Compliance ABNT) não encontrada no PRD.")
    trecho = texto[bloco_inicio:]
    out: dict[str, str] = {}
    for m in MD_ABNT_HEADER.finditer(trecho):
        codigo, titulo_eixo = m.group(1), m.group(2).strip()
        out[codigo] = titulo_eixo
    return out


def main() -> int:
    raiz = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    perguntas = raiz.get("perguntas", [])
    esperado_md = _esperado_md_por_codigo()
    erros: list[str] = []

    for item in perguntas:
        codigo = str(item.get("codigo", ""))
        if not codigo.startswith("Q-ABNT-"):
            continue
        pilar = item.get("pilar_abnt")
        if not pilar or not str(pilar).strip():
            erros.append(f"{codigo}: pilar_abnt ausente no JSON.")
            continue
        titulo_doc = esperado_md.get(codigo)
        if not titulo_doc:
            erros.append(f"{codigo}: cabeçalho ### não encontrado no PRD (secção 8).")
            continue
        # O JSON deve espelhar capítulo + eixo do doc (``pilar_abnt`` contém prefixo normativo).
        if titulo_doc not in str(pilar):
            erros.append(
                f"{codigo}: pilar_abnt não contém o eixo do PRD ({titulo_doc!r}). "
                f"Valor actual: {pilar!r}"
            )

    if erros:
        print("auditoria_pilar_abnt_catalogo: FALHA", file=sys.stderr)
        for e in erros:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("auditoria_pilar_abnt_catalogo: OK (Q-ABNT-* coerentes com PRD secção 8).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
