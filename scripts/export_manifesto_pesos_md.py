#!/usr/bin/env python3
"""
Gera artefacto Markdown do manifesto de pesos a partir do catálogo JSON.

Uso:
  PYTHONPATH=. python scripts/export_manifesto_pesos_md.py

Saída: docs/refs/MANIFESTO_PESOS_EXPORTADO.md (sobrescrita).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    data_path = _root() / "src/infrastructure/questionario/data/perguntas_mvp.json"
    out_path = _root() / "docs/refs/MANIFESTO_PESOS_EXPORTADO.md"

    raw = json.loads(data_path.read_text(encoding="utf-8"))
    perguntas = raw.get("perguntas", [])
    if not isinstance(perguntas, list):
        raise SystemExit("JSON sem lista 'perguntas'.")

    linhas: list[str] = [
        "# Manifesto de pesos — exportação do catálogo MVP",
        "",
        f"> **Gerado automaticamente em:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC  ",
        "> **Fonte:** `src/infrastructure/questionario/data/perguntas_mvp.json`  ",
        "> **Canónico em runtime:** `GET /diagnosticos/manifesto-pesos` e `GET /diagnosticos/metodologia` (com `DATABASE_URL` + migração **0015** para pesos macro).",
        "",
        "| Código | Dimensão | Peso | Tipo | Pilar ABNT (editorial) |",
        "|--------|----------|------|------|-------------------------|",
    ]

    for p in perguntas:
        if not isinstance(p, dict):
            continue
        codigo = str(p.get("codigo", ""))
        dim = str(p.get("dimensao", ""))
        peso = p.get("peso", "")
        tipo = str(p.get("tipo", ""))
        pilar = str(p.get("pilar_abnt") or "—")
        linhas.append(f"| {codigo} | {dim} | {peso} | {tipo} | {pilar} |")

    linhas.extend(
        [
            "",
            "## Regenerar",
            "",
            "```bash",
            "PYTHONPATH=. python scripts/export_manifesto_pesos_md.py",
            "```",
            "",
        ]
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"Escrito: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
