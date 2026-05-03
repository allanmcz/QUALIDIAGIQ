#!/usr/bin/env python3
"""
CLI da auditoria do catálogo MVP — delega em ``catalogo_auditoria``.

Uso:
  PYTHONPATH=. python scripts/auditoria_catalogo_perguntas_mvp.py
  python scripts/auditoria_catalogo_perguntas_mvp.py --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.infrastructure.questionario.catalogo_auditoria import auditar_catalogo_perguntas_mvp


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_json() -> Path:
    return _repo_root() / "src" / "infrastructure" / "questionario" / "data" / "perguntas_mvp.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoria catálogo perguntas MVP.")
    parser.add_argument("--json", type=str, default="", help="Caminho ao JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Falha se pilar_abnt ausente.",
    )
    args = parser.parse_args()
    path = Path(args.json) if args.json.strip() else _default_json()
    if not path.is_file():
        print(f"Ficheiro não encontrado: {path}", file=sys.stderr)
        return 2

    erros, avisos = auditar_catalogo_perguntas_mvp(str(path), strict_pilar_abnt=args.strict)
    for a in avisos:
        print(f"[aviso] {a}")
    if erros:
        print("Auditoria: FALHA", file=sys.stderr)
        for e in erros:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("Auditoria catálogo MVP: OK (invariantes estruturais).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
