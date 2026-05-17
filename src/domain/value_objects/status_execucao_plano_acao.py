"""
Value object: status operacional do Kanban sobre o plano materializado.

Camada: Domain
Base normativa: operacional QDI (ABNT NBR 17301:2026 — rastreabilidade de execução).
"""

from __future__ import annotations

from enum import StrEnum


class StatusExecucaoPlanoAcao(StrEnum):
    """Colunas Kanban Onda 1.0 — persistidas em ``diagnostico_plano_acao_estado``."""

    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    BLOQUEADO = "bloqueado"
    CONCLUIDA = "concluida"

    @classmethod
    def valores_validos(cls) -> frozenset[str]:
        return frozenset(m.value for m in cls)
