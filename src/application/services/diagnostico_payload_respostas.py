"""
Extrai entradas de resposta a partir do dict JSON do rascunho (sem Pydantic da camada HTTP).

Camada: Application — backfill e reidratação offline.
"""

from __future__ import annotations

from typing import Any

from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.infrastructure.questionario.banco_cache import get_banco_perguntas_cached


def entradas_resposta_de_payload_dict(payload: dict[str, Any]) -> list[EntradaRespostaDiagnostico]:
    """Mapeia ``respostas`` do corpo JSON para entradas de domínio."""
    respostas_raw = payload.get("respostas")
    if not isinstance(respostas_raw, list) or not respostas_raw:
        raise ValueError("Payload sem lista respostas")
    banco = get_banco_perguntas_cached()
    mapa = {p.id: p for p in banco}
    entradas: list[EntradaRespostaDiagnostico] = []
    for item in respostas_raw:
        if not isinstance(item, dict):
            raise ValueError("Item de resposta inválido")
        pid = item.get("pergunta_id")
        if pid is None:
            raise ValueError("Resposta sem pergunta_id")
        pergunta = mapa.get(str(pid))
        if pergunta is None:
            raise ValueError(f"Pergunta não encontrada no catálogo: {pid}")
        entradas.append(
            EntradaRespostaDiagnostico(pergunta=pergunta, valor_bruto=item.get("valor"))
        )
    return entradas
