"""
Snapshot HTTP do plano de ação materializado (checklist + matriz + cronograma).

Camada: Domain (value object leve — transporta dados já serializáveis vindos da infra).

Base normativa: ABNT NBR 17301:2026 cap. 7 (rastreio de evidências operacionais); LC 214/2025.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PlanoPainelSerializado:
    """Payload canónico do painel após leitura da BD (ou derivação única na finalização)."""

    versao_plano: int
    checklist: tuple[dict[str, Any], ...]
    matriz_impacto: tuple[dict[str, Any], ...]
    cronograma: tuple[dict[str, Any], ...]
    subtarefas_por_acao: dict[str, tuple[dict[str, Any], ...]] = field(default_factory=dict)
