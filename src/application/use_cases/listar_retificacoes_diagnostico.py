"""
Lista retificações de um diagnóstico (cadeia temporal).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.application.ports.diagnostico_retificacao_port import (
    DiagnosticoRetificacaoPort,
    DiagnosticoRetificacaoRegisto,
)


@dataclass(frozen=True)
class ComandoListarRetificacoesDiagnostico:
    """Parâmetros de listagem."""

    tenant_id: UUID
    diagnostico_original_id: UUID
    limit: int = 50


class ListarRetificacoesDiagnostico:
    """Delega ao port Postgres."""

    def __init__(self, *, retificacao: DiagnosticoRetificacaoPort) -> None:
        self._ret = retificacao

    async def execute(
        self, comando: ComandoListarRetificacoesDiagnostico
    ) -> list[DiagnosticoRetificacaoRegisto]:
        return await self._ret.listar_por_diagnostico(
            tenant_id=comando.tenant_id,
            diagnostico_original_id=comando.diagnostico_original_id,
            limit=min(comando.limit, 200),
        )
