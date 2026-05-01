"""Cache por processo do catálogo `perguntas_mvp.json` (evita reler disco a cada request)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.infrastructure.questionario.json_banco_loader import carregar_banco_mvp

if TYPE_CHECKING:
    from src.domain.entities.questionario import Pergunta

_CACHE: list[Pergunta] | None = None


def get_banco_perguntas_cached() -> list[Pergunta]:
    global _CACHE
    if _CACHE is None:
        _CACHE = carregar_banco_mvp()
    return _CACHE


def versao_catalogo_lida() -> str:
    """Lê `versao_catalogo` do JSON sem hidratar entidades."""
    import json

    from src.infrastructure.questionario.json_banco_loader import _ARQUIVO_PADRAO

    raw = json.loads(_ARQUIVO_PADRAO.read_text(encoding="utf-8"))
    return str(raw.get("versao_catalogo", "unknown"))
