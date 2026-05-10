"""
Validação JSON Schema do pacote de export (infraestrutura).

Camada: Infrastructure
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def _schema_path() -> Path:
    """Resolve ``docs/schemas/qdi-diagnostico-export-v1.schema.json`` a partir da raiz do repo."""
    here = Path(__file__).resolve()
    root = here.parents[3]  # exportacao → infrastructure → src → raiz
    return root / "docs" / "schemas" / "qdi-diagnostico-export-v1.schema.json"


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    path = _schema_path()
    import json

    with path.open(encoding="utf-8") as f:
        schema = json.load(f)
    return Draft202012Validator(schema)


def validar_payload_export_diagnostico_v1(payload: dict[str, Any]) -> None:
    """Raises ``jsonschema.ValidationError`` se o payload não cumprir o schema."""
    v = _validator()
    errors = sorted(v.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        raise errors[0]
