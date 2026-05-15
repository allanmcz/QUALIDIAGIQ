"""
Referência rastreável a base normativa ou técnica (evidência para RAG).

Camada: Domain
Imutável — usada pelo guardrail para impedir resposta «solta» sem âncora citável.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Referência mínima para auditoria e citação no texto de saída."""

    fonte: str
    titulo: str
    dispositivo: str
    url: str | None = None
    hash_conteudo: str | None = None
