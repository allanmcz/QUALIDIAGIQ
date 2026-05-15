"""
Extrai texto seguro da narrativa LLM para leitura pública (self-service).

Camada: Application — sem metadados de provider/custo na resposta HTTP pública.
"""

from __future__ import annotations

from typing import Any


def texto_explicacao_score_para_leitura_publica(
    snapshot: dict[str, Any] | None,
) -> str | None:
    """
    Devolve apenas o texto narrativo se existir e não estiver bloqueado por guardrail.

    Returns:
        Texto para UI pública ou ``None`` se indisponível.
    """
    if not isinstance(snapshot, dict):
        return None
    if snapshot.get("blocked_by_guardrail") is True:
        return None
    raw = snapshot.get("text")
    if not isinstance(raw, str):
        return None
    texto = raw.strip()
    return texto if texto else None
