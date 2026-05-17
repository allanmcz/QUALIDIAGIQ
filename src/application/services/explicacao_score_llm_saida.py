"""
Classificação da saída LLM — explicação do score (parecer consultivo, não fallback de adapter).

Camada: Application
"""

from __future__ import annotations

# Fragmentos de mensagens genéricas dos adapters (não são parecer sobre o diagnóstico).
_MARCADORES_FALLBACK_ADAPTER: tuple[str, ...] = (
    "indisponibilidade temporária",
    "recomendação não gerada pelo modelo",
    "erro ao processar a recomendação",
)

_MIN_CARACTERES_PARECER = 80


def parecer_explicacao_score_substantivo(texto: str) -> bool:
    """
    True se o texto parece parecer consultivo (não rejeição Lexiq nem erro de adapter).

    Usado no guardrail, no snapshot persistido e na validação do router.
    """
    out = (texto or "").strip()
    if len(out) < _MIN_CARACTERES_PARECER:
        return False
    if out.startswith("Recomendação não exibida:"):
        return False
    baixo = out.casefold()
    return not any(m in baixo for m in _MARCADORES_FALLBACK_ADAPTER)
