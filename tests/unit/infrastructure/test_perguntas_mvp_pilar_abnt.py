"""Garante pilares ABNT no catálogo MVP alinhados ao PRD (secção 8 — Bloco 5)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from src.infrastructure.questionario.json_banco_loader import carregar_banco_mvp

# tests/unit/infrastructure/ → raiz do repositório = 4 níveis acima
ROOT = Path(__file__).resolve().parents[3]


class TestCatalogoPilarAbnt:
    """Loader + contagens — auditoria formal repete em ``scripts/auditoria_pilar_abnt_catalogo.py``."""

    def test_carrega_37_perguntas(self) -> None:
        banco = carregar_banco_mvp()
        assert len(banco) == 37

    def test_questoes_abnt_tem_pilar_com_eixo_do_prd(self) -> None:
        data = json.loads(
            (ROOT / "src/infrastructure/questionario/data/perguntas_mvp.json").read_text(
                encoding="utf-8"
            )
        )
        md = (ROOT / "docs/refs/05_QUESTIONARIO_v1.md").read_text(encoding="utf-8")
        for item in data["perguntas"]:
            codigo = item["codigo"]
            if not str(codigo).startswith("Q-ABNT-"):
                continue
            pilar = item.get("pilar_abnt")
            assert pilar and str(pilar).strip(), f"{codigo} deve ter pilar_abnt preenchido."
            # Cabeçalho no PRD: ### Q-ABNT-00N — Eixo ...
            needle = f"### {codigo}"
            idx = md.find(needle)
            assert idx >= 0, f"Código {codigo} não encontrado no PRD."
            linha_fim = md.find("\n", idx)
            header = md[idx:linha_fim] if linha_fim > idx else md[idx:]
            parte_eixo = header.split("—", 1)[1].strip() if "—" in header else ""
            assert parte_eixo, f"Cabeçalho PRD sem eixo: {header!r}"
            assert parte_eixo in str(
                pilar
            ), f"{codigo}: pilar deve citar o eixo do PRD: {parte_eixo!r}"

    def test_script_auditoria_exit_zero(self) -> None:
        script = ROOT / "scripts" / "auditoria_pilar_abnt_catalogo.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PYTHONPATH": str(ROOT)},
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
