"""
Caso de uso — exclusão administrativa de diagnósticos por CNPJ (painel consultor).

Camada: Application

Remove fisicamente todos os diagnósticos do tenant com o CNPJ informado que ainda
não estão ``finalizado`` (sem solicitação LGPD individual — limpeza operacional).
Diagnósticos finalizados permanecem; o cliente deve usar fluxo LGPD por ciclo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.errors import EliminacaoEmpresaSomenteWormError
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.resultado_eliminacao_empresa import ResultadoEliminacaoEmpresa

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoEliminarDiagnosticosEmpresaPainel:
    tenant_id: UUID
    actor_user_id: UUID
    empresa_cnpj: str


class EliminarDiagnosticosEmpresaPainel:
    """Orquestra validação de CNPJ e eliminação em lote no repositório."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(
        self, cmd: ComandoEliminarDiagnosticosEmpresaPainel
    ) -> ResultadoEliminacaoEmpresa:
        resultado = await self._repo.eliminar_diagnosticos_empresa_eliminaveis(
            cmd.tenant_id,
            cmd.empresa_cnpj,
            actor_user_id=cmd.actor_user_id,
        )
        if resultado.total_encontrados == 0:
            raise ValueError(
                "Nenhum diagnóstico encontrado para esta empresa no seu painel."
            )
        if resultado.total_eliminados == 0:
            if resultado.mantidos_finalizados > 0:
                raise EliminacaoEmpresaSomenteWormError(
                    "Todos os diagnósticos desta empresa estão finalizados (evidência WORM). "
                    "Use Privacidade LGPD para anonimização ou eliminação por ciclo, conforme o caso."
                )
            raise ValueError(
                "Nenhum diagnóstico elegível para exclusão nesta empresa "
                "(estados admissíveis: em andamento, cancelado ou expirado)."
            )
        return resultado
