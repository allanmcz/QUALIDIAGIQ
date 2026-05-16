"""
Evidência citável mínima para itens do plano (recusa controlada no motor).

Camada: Domain
Princípio Tributiq: score de similaridade abaixo do limiar ⇒ evidência inválida.

Sprint 1 (motor determinístico): ``chunk_id`` sintético estável (uuid5) — Sprint 2 liga a Lexiq real.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date  # noqa: TC003 — usado em ``__post_init__`` em runtime
from uuid import UUID  # noqa: TC003 — tipo de campo congelado

LIMIAR_RECUSA_CONTROLADA: float = 0.65


@dataclass(frozen=True, slots=True)
class EvidenciaLexiq:
    """Âncora normativa mínima para persistência e auditoria."""

    norma: str
    dispositivo: str
    versao: str
    vigencia_inicio: date
    vigencia_fim: date | None
    chunk_id: UUID
    citacao_texto: str
    score_similaridade: float

    def __post_init__(self) -> None:
        if self.score_similaridade < LIMIAR_RECUSA_CONTROLADA:
            raise ValueError(
                f"Score {self.score_similaridade:.3f} abaixo do limiar "
                f"de recusa controlada ({LIMIAR_RECUSA_CONTROLADA})"
            )
        if not self.citacao_texto or len(self.citacao_texto) > 500:
            raise ValueError("citacao_texto deve ter 1-500 caracteres")
