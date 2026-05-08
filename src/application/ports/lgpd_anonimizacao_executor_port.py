"""
Executor de anonimização LGPD (PII respondente) sob WORM.

Camada: Application — interface; implementação em ``postgres_lgpd_anonimizacao_executor_adapter``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class LgpdAnonimizacaoExecutorPort(ABC):
    """Aplica padrão sentinel de anonimização + trilha ``lgpd_anonimizacao_log``."""

    @abstractmethod
    async def aplicar_anonimizacao_respondente(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        """
        Exige diagnóstico ``finalizado``. Atualiza apenas campos do respondente permitidos pelo trigger WORM.
        Conclui solicitação ``deferida`` na mesma transação.
        """
