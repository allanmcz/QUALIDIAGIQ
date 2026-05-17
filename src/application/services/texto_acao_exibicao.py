"""
Texto de ações do plano — normalização para exibição (sem metadado de lacuna/score).

Camada: Application
"""

from __future__ import annotations

import re
from typing import Any

# Sufixo legado M07: «— lacuna «Contábil» (score 17.9/100).»
_SUFIXO_LACUNA_SCORE_RE = re.compile(
    r"\s*—\s*lacuna\s*«[^»]+»\s*\(score\s*[\d.,]+\s*/\s*100\)\.?$",
    re.IGNORECASE,
)


def limpar_sufixo_lacuna_score_acao(texto: str) -> str:
    """Remove o sufixo automático de dimensão/score do texto canônico da ação."""
    if not texto:
        return texto
    return _SUFIXO_LACUNA_SCORE_RE.sub("", texto).strip()


def sanitizar_descricoes_checklist_serializado(
    checklist: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Limpa descrições no payload HTTP do checklist (plano materializado ou motor legado)."""
    out: list[dict[str, Any]] = []
    for frente in checklist:
        f = dict(frente)
        acoes_limpas: list[dict[str, Any]] = []
        for acao in f.get("acoes") or []:
            a = dict(acao)
            desc = a.get("descricao")
            if isinstance(desc, str):
                a["descricao"] = limpar_sufixo_lacuna_score_acao(desc)
            acoes_limpas.append(a)
        f["acoes"] = acoes_limpas
        out.append(f)
    return out
