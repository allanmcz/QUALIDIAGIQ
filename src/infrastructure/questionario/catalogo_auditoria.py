"""
Auditoria estrutural do JSON de perguntas MVP (G1 — invariantes de catálogo).

Camada: Infrastructure (ferramenta de validação; sem regras de domínio de score).
"""

from __future__ import annotations

import json

TIPOS_PERGUNTA_OK = frozenset(
    {
        "ternaria",
        "binaria",
        "escala_1_5",
        "multipla_escolha",
        "checklist",
        "numerica",
    },
)


def auditar_catalogo_perguntas_mvp(
    path: str,
    *,
    esperado_perguntas: int = 37,
    strict_pilar_abnt: bool = False,
) -> tuple[list[str], list[str]]:
    """
    Valida ``perguntas_mvp.json``.

    Args:
        path: Caminho absoluto ou relativo ao ficheiro JSON.

    Returns:
        (erros_bloqueantes, avisos)
    """
    from pathlib import Path

    erros: list[str] = []
    avisos: list[str] = []

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    perguntas = data.get("perguntas")
    if not isinstance(perguntas, list):
        return (["Campo 'perguntas' deve ser lista."], avisos)

    n = len(perguntas)
    if n != esperado_perguntas:
        erros.append(f"Esperadas {esperado_perguntas} perguntas; encontradas {n}.")

    for p in perguntas:
        if not isinstance(p, dict):
            erros.append("Entrada não-objeto em 'perguntas'.")
            continue
        cod = str(p.get("codigo", "?"))
        tipo = str(p.get("tipo", "")).strip()
        if tipo not in TIPOS_PERGUNTA_OK:
            erros.append(f"{cod}: tipo inválido «{tipo}».")
        if tipo in ("multipla_escolha", "checklist"):
            mt = p.get("multipla_total")
            if mt is None or (isinstance(mt, int) and mt < 1):
                erros.append(f"{cod}: multipla_escolha/checklist exige multipla_total >= 1.")
        pilar = p.get("pilar_abnt")
        if not pilar or (isinstance(pilar, str) and not pilar.strip()):
            msg = f"{cod}: pilar_abnt ausente ou vazio (alinhamento ABNT 37x35)."
            if strict_pilar_abnt:
                erros.append(msg)
            else:
                avisos.append(msg)

    return (erros, avisos)
