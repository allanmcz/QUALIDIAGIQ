"""
Entidades e regras de negócio para o motor do questionário.

Camada: Domain
Isola toda a complexidade de exibição condicional e pontuação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from src.domain.entities.diagnostico import EmpresaInfo, RegimeTributario, SetorMacro
from src.domain.value_objects.score import Dimensao


class TipoPergunta(Enum):
    TERNARIA = "ternaria"
    ESCALA_1_5 = "escala_1_5"


class AlternativaTernaria(Enum):
    SIM = "sim"
    PARCIALMENTE = "parcialmente"
    NAO = "nao"


@dataclass(frozen=True, slots=True)
class CondicaoExibicao:
    """Regras para o motor adaptativo decidir se a pergunta aparece."""

    regimes_permitidos: tuple[RegimeTributario, ...] | None = None
    setores_permitidos: tuple[SetorMacro, ...] | None = None


@dataclass(frozen=True, slots=True)
class Pergunta:
    """Uma questão dentro do diagnóstico."""

    codigo: str
    dimensao: Dimensao
    texto: str
    peso: float
    tipo: TipoPergunta
    base_legal: str | None = None
    condicao: CondicaoExibicao | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.peso < 0:
            raise ValueError(f"Peso não pode ser negativo. Recebido: {self.peso}")

    def aplicavel_para(self, empresa: EmpresaInfo) -> bool:
        """
        Avalia se a pergunta é aplicável para a empresa (Motor Adaptativo).
        Se a pergunta não tem condição, ela é "core" e se aplica a todos.
        """
        if self.condicao is None:
            return True

        if self.condicao.regimes_permitidos is not None:
            if empresa.regime not in self.condicao.regimes_permitidos:
                return False

        if self.condicao.setores_permitidos is not None:
            if empresa.setor_macro not in self.condicao.setores_permitidos:
                return False

        return True


@dataclass(frozen=True, slots=True)
class Resposta:
    """Resposta dada pelo usuário a uma pergunta."""

    diagnostico_id: UUID
    pergunta_id: UUID
    pergunta_tipo: TipoPergunta
    valor_bruto: str | int  # 'sim', 'nao', 1, 5, etc.
    id: UUID = field(default_factory=uuid4)

    def calcular_pontuacao(self) -> float:
        """Converte a resposta bruta em pontuação de 0 a 100."""
        if self.pergunta_tipo == TipoPergunta.TERNARIA:
            try:
                alternativa = AlternativaTernaria(str(self.valor_bruto).lower())
            except ValueError:
                raise ValueError(
                    f"Valor inválido para pergunta ternária: {self.valor_bruto}. "
                    f"Use 'sim', 'parcialmente' ou 'nao'."
                )
            if alternativa == AlternativaTernaria.SIM:
                return 100.0
            if alternativa == AlternativaTernaria.PARCIALMENTE:
                return 50.0
            return 0.0

        if self.pergunta_tipo == TipoPergunta.ESCALA_1_5:
            try:
                escala = int(self.valor_bruto)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Valor inválido para escala. Deve ser um número de 1 a 5. Recebido: {self.valor_bruto}"
                )
            if not 1 <= escala <= 5:
                raise ValueError(f"Valor fora do limite da escala (1-5): {escala}")
            # Regra: 1=0, 2=25, 3=50, 4=75, 5=100
            return (escala - 1) * 25.0

        raise NotImplementedError(f"Cálculo não implementado para o tipo {self.pergunta_tipo}")
