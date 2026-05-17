"""DTO de entrada — pergunta aplicada + valor bruto do questionário."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.questionario import Pergunta


@dataclass(frozen=True)
class EntradaRespostaDiagnostico:
    """Par pergunta aplicada + valor bruto — `diagnostico_id` preenchido no use case."""

    pergunta: Pergunta
    valor_bruto: str | int | list[str]
