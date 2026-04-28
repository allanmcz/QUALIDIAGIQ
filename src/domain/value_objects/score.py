"""
Value Objects relativos a Score (pontuação) do diagnóstico.

Camada: Domain
Imutáveis (frozen=True) por princípio DDD — value objects não têm identidade própria.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Dimensao(Enum):
    """
    Dimensões avaliadas pelo QDI.

    Mapeamento:
        - 6 dimensões herdadas da Cosmos Advisors (Radar Reforma)
        - 7ª dimensão (COMPLIANCE_ABNT) é diferencial exclusivo do QDI,
          ancorada na ABNT NBR 17301:2026
    """

    FISCAL = "fiscal"
    ESTRATEGICA = "estrategica"
    CONTABIL = "contabil"
    FINANCEIRA = "financeira"
    OPERACIONAL = "operacional"
    TECNOLOGICA = "tecnologica"
    COMPLIANCE_ABNT = "compliance_abnt_17301"  # diferencial QDI


class NivelMaturidade(Enum):
    """
    Faixas qualitativas derivadas do score numérico.

    Calibração inicial (revisar com cases reais):
        - 0-20:    CRITICO
        - 21-40:   INICIAL
        - 41-60:   INTERMEDIARIO
        - 61-80:   AVANCADO
        - 81-100:  EXEMPLAR
    """

    CRITICO = "critico"
    INICIAL = "inicial"
    INTERMEDIARIO = "intermediario"
    AVANCADO = "avancado"
    EXEMPLAR = "exemplar"

    @classmethod
    def from_score(cls, score: float) -> NivelMaturidade:
        """Converte um score 0-100 no nível qualitativo correspondente."""
        if not 0.0 <= score <= 100.0:
            raise ValueError(f"Score inválido: {score}. Deve estar entre 0 e 100.")
        if score <= 20:
            return cls.CRITICO
        if score <= 40:
            return cls.INICIAL
        if score <= 60:
            return cls.INTERMEDIARIO
        if score <= 80:
            return cls.AVANCADO
        return cls.EXEMPLAR


@dataclass(frozen=True, slots=True)
class ScoreNumerico:
    """
    Pontuação 0-100 com transparência metodológica.

    Princípio (de Cosmos Advisors): "não há caixa-preta — você entende
    exatamente de onde vêm os resultados."

    Atributos:
        valor: float em [0, 100]
        peso_total_aplicado: soma dos pesos de todas as perguntas consideradas
        perguntas_consideradas: códigos das perguntas que entraram no cálculo
    """

    valor: float
    peso_total_aplicado: float
    perguntas_consideradas: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.valor <= 100.0:
            raise ValueError(f"Valor de score deve estar entre 0 e 100. Recebido: {self.valor}")
        if self.peso_total_aplicado < 0:
            raise ValueError("Peso total aplicado não pode ser negativo.")

    @property
    def nivel(self) -> NivelMaturidade:
        return NivelMaturidade.from_score(self.valor)


@dataclass(frozen=True, slots=True)
class ScoreCompleto:
    """
    Composição final do diagnóstico — score geral + scores por dimensão.

    Aderência:
        - Score geral é média ponderada dos scores por dimensão
        - Pesos por dimensão configuráveis (default igual = 1/N)
    """

    score_geral: ScoreNumerico
    score_por_dimensao: dict[Dimensao, ScoreNumerico]
    score_relativo_setor: PercentilSetorial | None = None

    def __post_init__(self) -> None:
        if len(self.score_por_dimensao) == 0:
            raise ValueError("ScoreCompleto deve conter ao menos uma dimensão avaliada.")


@dataclass(frozen=True, slots=True)
class PercentilSetorial:
    """
    Score relativo ao benchmark setorial (vantagem competitiva multi-tenant).

    Exemplo: percentil 35 entre varejistas do Sul de mesmo porte.
    """

    percentil: int  # 0-100
    setor_referencia: str
    porte_referencia: str
    uf_referencia: str | None
    n_amostra: int  # quantidade de empresas na coorte de referência

    def __post_init__(self) -> None:
        if not 0 <= self.percentil <= 100:
            raise ValueError(f"Percentil inválido: {self.percentil}.")
        if self.n_amostra < 1:
            raise ValueError("n_amostra deve ser ≥ 1.")
