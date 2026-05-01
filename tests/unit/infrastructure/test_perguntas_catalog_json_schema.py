"""Fase C1 — catalogo perguntas validado contra JSON Schema (analise execucao plano 11)."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_perguntas_mvp_obedece_schema() -> None:
    repo = Path(__file__).resolve().parents[3]
    catalogo_path = repo / "src/infrastructure/questionario/data/perguntas_mvp.json"
    schema_path = repo / "src/infrastructure/questionario/schema/perguntas_mvp.schema.json"
    blob = json.loads(catalogo_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(blob)
