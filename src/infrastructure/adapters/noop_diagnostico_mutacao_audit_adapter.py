"""Adaptador no-op para ``DiagnosticoMutacaoAuditPort`` quando não há DSN Postgres."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

from src.application.ports.diagnostico_mutacao_audit_port import (
    DiagnosticoMutacaoAuditPort,
    TipoMutacaoDiagnostico,
)


class NoOpDiagnosticoMutacaoAuditAdapter(DiagnosticoMutacaoAuditPort):
    """Não persiste auditoria (Supabase-only ou repositório em memória)."""

    async def registrar(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        tipo: TipoMutacaoDiagnostico,
        payload: dict[str, Any],
        actor_user_id: UUID | None,
        versao_otimista_antes: int,
        versao_otimista_apos: int,
    ) -> None:
        return None
