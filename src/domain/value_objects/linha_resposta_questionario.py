"""
Linha materializada de resposta ao questionário (snapshot por diagnóstico).

Camada: Domain — contrato de persistência e leitura para comparação entre ciclos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class LinhaRespostaQuestionario:
    """Uma pergunta respondida no diagnóstico, com texto e valor congelados na finalização."""

    ordem_exibicao: int
    pergunta_id: UUID
    pergunta_codigo: str
    dimensao: str
    tipo_pergunta: str
    texto_pergunta: str
    peso: float
    base_legal: str | None
    pilar_abnt: str | None
    valor_bruto: Any
    valor_exibicao: str
    pontuacao_item: float | None
    excluida_calculo: bool
