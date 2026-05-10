"""
Executor de eliminação física de diagnóstico (LGPD art. 18) quando não há WORM ativo.

Camada: Application — interface; implementação em ``postgres_lgpd_eliminacao_executor_adapter``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class LgpdEliminacaoExecutorPort(ABC):
    """Remove linha ``diagnosticos`` apenas em estados pré-evidência final (sem WORM de finalizado)."""

    @abstractmethod
    async def aplicar_eliminacao_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        """
        Exige solicitação ``eliminacao`` deferida e diagnóstico não ``finalizado``.
        Remove o agregado (cascata nas tabelas filhas) e conclui a solicitação na mesma transação.

        Raises:
            EliminacaoDiagnosticoFinalizadoWormError: status ``finalizado`` — usar anonimização.
            ValueError: pré-condições de negócio ou SQL (linha inexistente, etc.).
        """
