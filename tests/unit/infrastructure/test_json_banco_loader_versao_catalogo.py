"""Leitura de metadados do catálogo JSON (versão)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.infrastructure.questionario import json_banco_loader as jl


def test_versao_catalogo_banco_mvp_raiz_nao_objeto_retorna_unknown() -> None:
    """JSON corrompido ou raiz não-dict — manifesto não deve quebrar."""
    fake_path = MagicMock()
    fake_path.read_text.return_value = "[]"
    with patch.object(jl, "_ARQUIVO_PADRAO", fake_path):
        assert jl.versao_catalogo_banco_mvp() == "unknown"
