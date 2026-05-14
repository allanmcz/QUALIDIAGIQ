"""
Value object — peso de pergunta do catálogo com vigência normativa (DB).

Camada: Domain
Base normativa: LC 214/2025 (previsibilidade); ABNT NBR 17301:2026 (transparência M03).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


@dataclass(frozen=True, slots=True)
class PesoPerguntaNormativoVigente:
    """Linha efetiva de ``qdi.normativa_pergunta_peso`` na data de referência."""

    peso: float
    vigencia_inicio: date
    vigencia_fim: date | None
    rotulo_versao: str | None
