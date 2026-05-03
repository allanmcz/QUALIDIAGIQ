"""
Vinculação de leads no repositório em memória (CI Playwright / Compose padrão).

Camada: Infrastructure
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.ports.lead_diagnostico_vinculo_port import LeadDiagnosticoVinculoPort

if TYPE_CHECKING:
    from uuid import UUID
from src.infrastructure.repositories.ci_playwright_diagnostico_repository import (
    CiPlaywrightDiagnosticoRepository,
)


class MemoriaLeadDiagnosticoVinculoAdapter(LeadDiagnosticoVinculoPort):
    """Delega para `CiPlaywrightDiagnosticoRepository.vincular_leads_self_service_em_memoria`."""

    def __init__(self, repo: CiPlaywrightDiagnosticoRepository, tenant_self_service: UUID) -> None:
        self._repo = repo
        self._tenant_ss = tenant_self_service

    async def vincular_gratuitos_self_service_para_tenant(
        self,
        *,
        email_admin_normalizado: str,
        tenant_destino: UUID,
        tenant_self_service: UUID,
    ) -> list[UUID]:
        if tenant_self_service != self._tenant_ss:
            return []
        return self._repo.vincular_leads_self_service_em_memoria(
            tenant_self_service=tenant_self_service,
            tenant_destino=tenant_destino,
            email_admin_normalizado=email_admin_normalizado,
        )
