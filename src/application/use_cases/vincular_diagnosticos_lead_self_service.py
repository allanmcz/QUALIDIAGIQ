"""
Caso de uso: trazer diagnósticos gratuitos (self-service / OTP) para o tenant B2B do consultor.

Camada: Application

O e-mail do consultor deve ser resolvido antes (ex.: rota HTTP + `admins` no Postgres),
para manter este caso de uso dependente apenas do port de vinculação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.ports.lead_diagnostico_vinculo_port import LeadDiagnosticoVinculoPort

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoVincularDiagnosticosLeadSelfService:
    """E-mail já normalizado; tenants explícitos (origem self-service + destino B2B)."""

    email_admin_normalizado: str
    tenant_destino: UUID
    tenant_self_service: UUID


class VincularDiagnosticosLeadSelfService:
    """Delega ao port (Postgres sync ou memória CI)."""

    def __init__(self, vinculo: LeadDiagnosticoVinculoPort) -> None:
        self._vinculo = vinculo

    async def execute(self, comando: ComandoVincularDiagnosticosLeadSelfService) -> list[UUID]:
        return await self._vinculo.vincular_gratuitos_self_service_para_tenant(
            email_admin_normalizado=comando.email_admin_normalizado,
            tenant_destino=comando.tenant_destino,
            tenant_self_service=comando.tenant_self_service,
        )
