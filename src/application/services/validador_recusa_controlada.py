"""
Validador de recusa controlada para itens do plano (Sprint 1 + base Sprint 2).

Camada: Application
Princípios Tributiq nº 6 (similaridade) e nº 7 (evidência obrigatória).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from src.domain.entities.plano_acao import ItemAcao
from src.domain.value_objects.evidencia_lexiq import LIMIAR_RECUSA_CONTROLADA


@dataclass(frozen=True, slots=True)
class ResultadoValidacaoPlano:
    """Resultado estruturado (sem exceções no fluxo feliz)."""

    aprovado: bool
    motivo: str = ""
    metadata: dict[str, Any] | None = None

    @classmethod
    def ok(cls) -> ResultadoValidacaoPlano:
        return cls(aprovado=True)

    @classmethod
    def recusa(cls, motivo: str, **meta: Any) -> ResultadoValidacaoPlano:
        return cls(aprovado=False, motivo=motivo, metadata=meta or {})


class ValidadorRecusaControlada:
    """
    Garante evidências mínimas antes de persistir ``ItemAcao``.

    Sprint 1: validação local (VO já impõe score ≥ limiar).
    Sprint 2: revalidação com retriever Lexiq + cache.
    """

    def validar(self, item: ItemAcao, *, hoje: date | None = None) -> ResultadoValidacaoPlano:
        dia = hoje or date.today()
        if not item.evidencias:
            return ResultadoValidacaoPlano.recusa(
                "sem_evidencia_lexiq",
                codigo=item.codigo,
            )
        for evid in item.evidencias:
            if evid.score_similaridade < LIMIAR_RECUSA_CONTROLADA:
                return ResultadoValidacaoPlano.recusa(
                    "similaridade_insuficiente",
                    score=evid.score_similaridade,
                    norma=evid.norma,
                )
            if evid.vigencia_fim is not None and evid.vigencia_fim < dia:
                return ResultadoValidacaoPlano.recusa(
                    "norma_fora_vigencia",
                    norma=evid.norma,
                    vigencia_fim=str(evid.vigencia_fim),
                )
        return ResultadoValidacaoPlano.ok()
