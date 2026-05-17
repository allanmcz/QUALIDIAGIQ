"""
Adapter Postgres para arquivo de empresa no painel.

Camada: Infrastructure
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from src.application.ports.empresa_painel_arquivo_port import EmpresaPainelArquivoPort
from src.infrastructure.repositories.postgres_empresa_painel_arquivo_sync import (
    definir_arquivado_sync,
    esta_arquivada_sync,
    listar_cnpjs_arquivados_sync,
)


class PostgresEmpresaPainelArquivoAdapter(EmpresaPainelArquivoPort):
    """Implementação via ``DATABASE_URL`` (mesmo padrão dos repositórios sync QDI)."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def definir_arquivado(
        self,
        tenant_id: UUID,
        empresa_cnpj: str,
        *,
        arquivado: bool,
        actor_user_id: UUID | None = None,
    ) -> bool:
        return await asyncio.to_thread(
            definir_arquivado_sync,
            self._dsn,
            tenant_id,
            empresa_cnpj,
            arquivado=arquivado,
            actor_user_id=actor_user_id,
        )

    async def esta_arquivada(self, tenant_id: UUID, empresa_cnpj: str) -> bool:
        return await asyncio.to_thread(
            esta_arquivada_sync, self._dsn, tenant_id, empresa_cnpj
        )

    async def listar_cnpjs_arquivados(self, tenant_id: UUID) -> frozenset[str]:
        return await asyncio.to_thread(
            listar_cnpjs_arquivados_sync, self._dsn, tenant_id
        )
