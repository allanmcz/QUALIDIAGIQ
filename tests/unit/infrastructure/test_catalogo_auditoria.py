"""Testes da auditoria estrutural do catálogo MVP (G1)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.infrastructure.questionario.catalogo_auditoria import auditar_catalogo_perguntas_mvp


def _repo_root() -> Path:
    # tests/unit/infrastructure/ → raiz do repositório
    return Path(__file__).resolve().parent.parent.parent.parent


class TestAuditarCatalogoPerguntasMvp:
    """Invariantes sobre ficheiros temporários + script CLI."""

    def test_detecta_multipla_sem_total(self, tmp_path: Path) -> None:
        p = tmp_path / "x.json"
        p.write_text(
            json.dumps(
                {
                    "versao_catalogo": "t",
                    "perguntas": [
                        {
                            "codigo": "Q-X",
                            "tipo": "multipla_escolha",
                            "multipla_total": None,
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        erros, _ = auditar_catalogo_perguntas_mvp(str(p), esperado_perguntas=1)
        assert any("multipla_total" in e for e in erros)

    def test_strict_pilar_promove_aviso_a_erro(self, tmp_path: Path) -> None:
        p = tmp_path / "y.json"
        p.write_text(
            json.dumps(
                {
                    "versao_catalogo": "t",
                    "perguntas": [
                        {
                            "codigo": "Q-OK",
                            "tipo": "ternaria",
                            "pilar_abnt": "",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        _, avisos = auditar_catalogo_perguntas_mvp(
            str(p), esperado_perguntas=1, strict_pilar_abnt=False
        )
        assert avisos
        erros, _ = auditar_catalogo_perguntas_mvp(
            str(p), esperado_perguntas=1, strict_pilar_abnt=True
        )
        assert erros


@pytest.mark.parametrize("extra_args,expect_ok", [([], True), (["--strict"], False)])
def test_script_cli_exit_code(extra_args: list[str], expect_ok: bool) -> None:
    script = _repo_root() / "scripts" / "auditoria_catalogo_perguntas_mvp.py"
    cmd = [sys.executable, str(script), *extra_args]
    r = subprocess.run(
        cmd,
        cwd=str(_repo_root()),
        capture_output=True,
        text=True,
        check=False,
        env={**__import__("os").environ, "PYTHONPATH": str(_repo_root())},
    )
    if expect_ok:
        assert r.returncode == 0, r.stderr + r.stdout
    else:
        assert r.returncode == 1, r.stderr + r.stdout
