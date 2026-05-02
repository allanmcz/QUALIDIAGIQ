"""
Value Objects relativos a Score (pontuação) do diagnóstico.

Camada: Domain
Imutáveis (frozen=True) por princípio DDD — value objects não têm identidade própria.
"""

from __future__ import annotations

from collections.abc import Mapping  # noqa: TC003
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Final


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


# Agregação do score geral: média ponderada entre dimensões (M03 — mesmo núcleo do CalcularScore).
PESOS_MACRO_DIMENSAO_SCORE_GERAL: Final[dict[Dimensao, float]] = {
    Dimensao.FISCAL: 1.5,
    Dimensao.TECNOLOGICA: 1.3,
    Dimensao.COMPLIANCE_ABNT: 1.2,
    Dimensao.ESTRATEGICA: 1.0,
    Dimensao.CONTABIL: 1.0,
    Dimensao.FINANCEIRA: 1.0,
    Dimensao.OPERACIONAL: 1.0,
}


def pesos_macro_dimensao_para_dict_iso() -> dict[str, float]:
    """Representação estável `{dimensao.value: peso}` para API / manifestos."""
    return {d.value: float(w) for d, w in PESOS_MACRO_DIMENSAO_SCORE_GERAL.items()}


def exigir_mapa_pesos_macro_completo(pesos: Mapping[Dimensao, float]) -> None:
    """
    Invariante do motor M03: todas as dimensões devem ter peso macro positivo.

    Raises:
        ValueError: dimensão ausente ou peso não positivo.
    """
    for dim in Dimensao:
        if dim not in pesos:
            raise ValueError(
                f"Mapa de pesos macro incompleto: falta a dimensão '{dim.value}' "
                "(motor exige todas as 7 dimensões para transparência)."
            )
        p = float(pesos[dim])
        if p <= 0:
            raise ValueError(f"Peso macro da dimensão '{dim.value}' deve ser > 0; recebido {p}.")


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

    def para_dict_serializavel(self) -> dict[str, Any]:
        """Representação estável para JSONB (auditoria / hash de evidência)."""

        def _sn(sn: ScoreNumerico) -> dict[str, Any]:
            return {
                "valor": sn.valor,
                "peso_total_aplicado": sn.peso_total_aplicado,
                "perguntas_consideradas": list(sn.perguntas_consideradas),
            }

        dims: dict[str, Any] = {dim.value: _sn(sn) for dim, sn in self.score_por_dimensao.items()}
        out: dict[str, Any] = {
            "score_geral": _sn(self.score_geral),
            "score_por_dimensao": dims,
        }
        if self.score_relativo_setor is not None:
            sr = self.score_relativo_setor
            out["score_relativo_setor"] = {
                "percentil": sr.percentil,
                "setor_referencia": sr.setor_referencia,
                "porte_referencia": sr.porte_referencia,
                "uf_referencia": sr.uf_referencia,
                "n_amostra": sr.n_amostra,
            }
        return out

    @classmethod
    def desde_dict(cls, data: dict[str, Any]) -> ScoreCompleto:
        """Reidrata a partir do dict persistido em JSONB."""

        def _sn(raw: dict[str, Any]) -> ScoreNumerico:
            return ScoreNumerico(
                valor=float(raw["valor"]),
                peso_total_aplicado=float(raw["peso_total_aplicado"]),
                perguntas_consideradas=tuple(str(x) for x in raw.get("perguntas_consideradas", [])),
            )

        sg_raw = data["score_geral"]
        dims_raw: dict[str, Any] = data["score_por_dimensao"]
        por_dim: dict[Dimensao, ScoreNumerico] = {}
        for k, v in dims_raw.items():
            por_dim[Dimensao(k)] = _sn(v)

        rel: PercentilSetorial | None = None
        if data.get("score_relativo_setor"):
            sr = data["score_relativo_setor"]
            rel = PercentilSetorial(
                percentil=int(sr["percentil"]),
                setor_referencia=str(sr["setor_referencia"]),
                porte_referencia=str(sr["porte_referencia"]),
                uf_referencia=sr.get("uf_referencia"),
                n_amostra=int(sr["n_amostra"]),
            )

        return cls(
            score_geral=_sn(sg_raw),
            score_por_dimensao=por_dim,
            score_relativo_setor=rel,
        )


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
