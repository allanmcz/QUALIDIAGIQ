"""
Guardrail mínimo Lexiq / Tributiq — texto deve exibir âncora normativa reconhecível.

Camada: Application (regra de produto; sem dependência de infraestrutura de LLM).
Analogia: como uma constraint Oracle que impede INSERT sem FK válida — aqui sem fonte, não publicamos.
"""

from __future__ import annotations

import re

# Padrões amplos porém objetivos (S02 protótipo — evolução: IDs Lexiq versionados).
_PADROES_ANCORA = (
    re.compile(r"LC\s*214/2025"),
    re.compile(r"EC\s*132/2023"),
    re.compile(r"ABNT\s*NBR\s*17301"),
    re.compile(r"ABNT\s*NBR\s*ISO\s*37301", re.I),
    re.compile(r"NT\s*2025\.00[0-9]", re.I),
    re.compile(r"LC\s*225/2026"),
)


def texto_tem_ancora_normativa(texto: str) -> bool:
    """Retorna True se houver ao menos uma referência normativa detectável."""
    if not texto or not str(texto).strip():
        return False
    t = str(texto).strip()
    return any(p.search(t) for p in _PADROES_ANCORA)


def mensagem_rejeicao_guardrail() -> str:
    """Texto estável devolvido ao usuário quando a IA não cita base reconhecível."""
    return (
        "Recomendação não exibida: o texto gerado não continha âncora normativa verificável "
        "(ex.: LC 214/2025, EC 132/2023, ABNT NBR 17301:2026). "
        "Princípio Tributiq (Lexiq): sem citação válida, a resposta é rejeitada."
    )
