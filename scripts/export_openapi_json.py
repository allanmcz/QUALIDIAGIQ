#!/usr/bin/env python3
"""
Exporta o schema OpenAPI da app FastAPI para arquivo JSON (diff local, integradores).

Uso: PYTHONPATH=. python scripts/export_openapi_json.py
     make openapi-export
"""

from __future__ import annotations

import json
from pathlib import Path

from src.presentation.api.main import app

_ROOT = Path(__file__).resolve().parents[1]
_OUT = _ROOT / "docs" / "api" / "openapi.generated.json"


def main() -> None:
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()
    _OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Escrito: {_OUT}")


if __name__ == "__main__":
    main()
