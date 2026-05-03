"""
Port de reatribuição de tenant (lead self-service → conta na plataforma / painel).

Camada: Application (contrato — Dependency Inversion Principle)

Implementações: Postgres (bypass RLS com conexão app/sync) e memória CI Playwright.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class LeadDiagnosticoVinculoPort(ABC):
    """Move diagnósticos gratuitos do pool self-service para o tenant do consultor autenticado."""

    @abstractmethod
    async def vincular_gratuitos_self_service_para_tenant(
        self,
        *,
        email_admin_normalizado: str,
        tenant_destino: UUID,
        tenant_self_service: UUID,
    ) -> list[UUID]:
        """
        Reatribui `tenant_id` das linhas elegíveis.

        Critérios de elegibilidade (implementação concreta deve honrar):
        - `tenant_id` atual = tenant self-service configurado;
        - `respondente_email` coincide com o e-mail do admin (já normalizado);
        - plano gratuito (não promover automaticamente diagnóstico avançado de outro fluxo).

        Returns:
            Lista de IDs de diagnósticos atualizados (pode ser vazia).
        """
        ...


class NopLeadDiagnosticoVinculoAdapter(LeadDiagnosticoVinculoPort):
    """Sem `DATABASE_URL` sync — operação não disponível (retorna lista vazia)."""

    async def vincular_gratuitos_self_service_para_tenant(
        self,
        *,
        email_admin_normalizado: str,
        tenant_destino: UUID,
        tenant_self_service: UUID,
    ) -> list[UUID]:
        return []
