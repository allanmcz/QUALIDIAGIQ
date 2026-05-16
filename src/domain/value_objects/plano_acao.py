"""
Taxonomia canónica do plano de ação materializado (PDCA, horizonte, criticidade).

Camada: Domain (imutável)
Base normativa: ABNT NBR 17301:2026 cap. 6.1 (riscos); LC 214/2025 (transição 2026-2033).

Analogia Delphi: conjunto de ``TEnumeration`` com ordem estável para ``Case`` em relatórios.
"""

from __future__ import annotations

from enum import StrEnum


class CriticidadePlanoAcao(StrEnum):
    """Criticidade categórica persistível (motor + UI)."""

    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class HorizontePlanoAcao(StrEnum):
    """Horizonte temporal alinhado à transição LC 214/2025 (valores em MAIÚSCULAS = coluna SQL)."""

    IMEDIATO = "IMEDIATO"
    CURTO_PRAZO = "CURTO_PRAZO"
    MEDIO_PRAZO = "MEDIO_PRAZO"
    LONGO_PRAZO = "LONGO_PRAZO"
    ESTRATEGICO = "ESTRATEGICO"


class FasePdcaPlano(StrEnum):
    """Fase PDCA da ABNT NBR 17301:2026 (ciclo ISO 37301:2021)."""

    PLAN = "PLAN"
    DO = "DO"
    CHECK = "CHECK"
    ACT = "ACT"


class StatusExecucaoAcao(StrEnum):
    """Estado de acompanhamento no quadro de implantação (futuro PATCH dedicado)."""

    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    POSTERGADA = "postergada"
    NAO_APLICAVEL = "nao_aplicavel"
