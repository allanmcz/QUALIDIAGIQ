"""
Cálculo de criticidade categórica e metadados editoriais do plano.

Camada: Domain
Base normativa: ABNT NBR 17301:2026 cap. 6.1; LC 214/2025 (cronograma).
"""

from __future__ import annotations

import re
import unicodedata
from uuid import NAMESPACE_URL, UUID, uuid5

from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
)
from src.domain.value_objects.score import Dimensao

_MULTIPLICADOR_DIMENSAO: dict[str, float] = {
    Dimensao.FISCAL.value: 1.5,
    Dimensao.TECNOLOGICA.value: 1.3,
    Dimensao.COMPLIANCE_ABNT.value: 1.2,
    Dimensao.ESTRATEGICA.value: 1.0,
    Dimensao.CONTABIL.value: 1.0,
    Dimensao.FINANCEIRA.value: 1.0,
    Dimensao.OPERACIONAL.value: 1.0,
}


def computar_criticidade(
    peso_pergunta: float,
    ratio_resposta: float,
    dimensao: str,
) -> CriticidadePlanoAcao:
    """
    Severidade = peso * (1 - ratio) * multiplicador_dimensao -> faixa categórica.

    Args:
        peso_pergunta: peso 0..10.
        ratio_resposta: fração de desempenho 0..1 (1 = sem gap).
        dimensao: valor ``Dimensao.value``.
    """
    if dimensao not in _MULTIPLICADOR_DIMENSAO:
        raise ValueError(f"Dimensão desconhecida: {dimensao}")
    if not 0.0 <= ratio_resposta <= 1.0:
        raise ValueError(f"ratio_resposta={ratio_resposta} fora de [0, 1]")
    if not 0.0 <= peso_pergunta <= 10.0:
        raise ValueError(f"peso_pergunta={peso_pergunta} fora de [0, 10]")

    severidade = peso_pergunta * (1.0 - ratio_resposta) * _MULTIPLICADOR_DIMENSAO[dimensao]
    if severidade >= 12.0:
        return CriticidadePlanoAcao.CRITICA
    if severidade >= 8.0:
        return CriticidadePlanoAcao.ALTA
    if severidade >= 4.0:
        return CriticidadePlanoAcao.MEDIA
    return CriticidadePlanoAcao.BAIXA


def fase_pdca_default_para_dimensao(dimensao: str | None) -> FasePdcaPlano:
    """Mapeamento determinístico dimensão → fase PDCA default."""
    if not dimensao:
        return FasePdcaPlano.DO
    d = dimensao.strip().lower()
    if d == Dimensao.ESTRATEGICA.value:
        return FasePdcaPlano.PLAN
    if d == Dimensao.FINANCEIRA.value:
        return FasePdcaPlano.CHECK
    if d == Dimensao.COMPLIANCE_ABNT.value:
        return FasePdcaPlano.ACT
    return FasePdcaPlano.DO


def _norm_txt(s: str) -> str:
    n = unicodedata.normalize("NFKD", s.strip().casefold())
    return "".join(c for c in n if not unicodedata.combining(c))


def criticidade_rotulo_pt_para_enum(rotulo: str) -> CriticidadePlanoAcao:
    """Converte rótulo editorial (ex.: «Crítica») para código persistível."""
    t = _norm_txt(rotulo)
    if "crit" in t:
        return CriticidadePlanoAcao.CRITICA
    if "alt" in t:
        return CriticidadePlanoAcao.ALTA
    if "med" in t:
        return CriticidadePlanoAcao.MEDIA
    return CriticidadePlanoAcao.BAIXA


def inferir_horizonte_de_prazo_texto(prazo: str) -> HorizontePlanoAcao:
    """
    Heurística editorial: prazo textual → horizonte LC 214 / operacional.

    Não substitui calendário real — apenas classifica o texto do motor M07/M12.
    """
    t = prazo.strip().lower()
    if "longo" in t or "60-96" in t or "36-60" in t:
        return HorizontePlanoAcao.LONGO_PRAZO
    if "estrat" in t or "96" in t:
        return HorizontePlanoAcao.ESTRATEGICO
    if "médio" in t or "medio" in t or "médio prazo" in t:
        return HorizontePlanoAcao.MEDIO_PRAZO
    if "curto" in t and "prazo" in t:
        return HorizontePlanoAcao.CURTO_PRAZO
    m = re.search(r"(\d+)\s*(d|dia|dias)", t)
    if m:
        dias = int(m.group(1))
        if dias <= 30:
            return HorizontePlanoAcao.IMEDIATO
        if dias <= 90:
            return HorizontePlanoAcao.CURTO_PRAZO
        return HorizontePlanoAcao.MEDIO_PRAZO
    if re.match(r"^[a-z]{3}/\d{4}$", t):
        return HorizontePlanoAcao.CURTO_PRAZO
    return HorizontePlanoAcao.CURTO_PRAZO


def chunk_id_sintetico_para_texto(texto: str) -> UUID:
    """UUID determinístico (uuid5) — substituível por chunk Lexiq na Sprint 2."""
    return uuid5(NAMESPACE_URL, texto[:400])
