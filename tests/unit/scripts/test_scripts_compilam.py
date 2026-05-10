"""Garante que os CLIs em ``scripts/*.py`` são sintaticamente válidos (sem executar I/O)."""

from __future__ import annotations

import compileall
from pathlib import Path


class TestScriptsPythonCompilam:
    """Analogia: ``dcc32 -cc`` no Delphi — validação de sintaxe antes de ligar dependências."""

    def test_diretorio_scripts_compila_sem_erro(self) -> None:
        raiz = Path(__file__).resolve().parents[3]
        scripts = raiz / "scripts"
        assert scripts.is_dir(), f"diretório scripts ausente: {scripts}"
        ok = compileall.compile_dir(
            str(scripts),
            quiet=1,
            legacy=False,
            optimize=0,
        )
        assert ok, "compileall encontrou erros de sintaxe em scripts/"
