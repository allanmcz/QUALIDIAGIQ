"""
Resultado da eliminação física de diagnósticos por empresa (CNPJ) no painel.

Camada: Domain (value object — sem dependências externas)

Base normativa / produto:
- ADR-012 — diagnósticos ``finalizado`` permanecem sob WORM; exclusão em massa só
  remove estados ``em_andamento``, ``cancelado`` ou ``expirado``.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ResultadoEliminacaoEmpresa:
    """Contagem e IDs após DELETE físico dos elegíveis no tenant."""

    empresa_cnpj: str
    eliminados_ids: tuple[UUID, ...]
    mantidos_finalizados: int
    mantidos_outros_status: int

    @property
    def total_eliminados(self) -> int:
        return len(self.eliminados_ids)

    @property
    def total_encontrados(self) -> int:
        return (
            self.total_eliminados + self.mantidos_finalizados + self.mantidos_outros_status
        )
