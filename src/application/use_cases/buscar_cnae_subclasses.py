"""
Caso de uso — busca auxiliar de CNAE no wizard (M01).

Camada: Application

Base legal contextual: cadastro econômico é insumo fiscal na Reforma do Consumo
(EC 132/2023, LC 214/2025 — classificação de contribuinte e cadeias).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.application.ports.cnae_subclasse_consulta_port import CnaeSubclasseConsultaPort
    from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo


@dataclass(frozen=True, slots=True)
class BuscarCnaeSubclasses:
    """Orquestra lookup CNAE via port injetado (Postgres em infra)."""

    repo: CnaeSubclasseConsultaPort

    async def execute(self, consulta: str, limite: int = 20) -> list[CnaeSubclasseResumo]:
        q = (consulta or "").strip()
        if len(q) < 2:
            raise ValueError("Informe ao menos 2 caracteres para buscar CNAE.")
        lim = max(1, min(int(limite), 50))
        return await self.repo.buscar(consulta=q, limite=lim)
