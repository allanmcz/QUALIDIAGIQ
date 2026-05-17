"""
Adapter em memória para arquivo de empresa (CI Playwright / testes sem Postgres).

Camada: Infrastructure
"""

from __future__ import annotations

from uuid import UUID

from src.application.ports.empresa_painel_arquivo_port import EmpresaPainelArquivoPort

_arquivados: set[tuple[str, str]] = set()


class MemoriaEmpresaPainelArquivoAdapter(EmpresaPainelArquivoPort):
    """Estado global de arquivo por (tenant_id, cnpj) — apenas dev/CI."""

    async def definir_arquivado(
        self,
        tenant_id: UUID,
        empresa_cnpj: str,
        *,
        arquivado: bool,
        actor_user_id: UUID | None = None,
    ) -> bool:
        _ = actor_user_id
        chave = (str(tenant_id), empresa_cnpj)
        if arquivado:
            if chave in _arquivados:
                return False
            _arquivados.add(chave)
            return True
        if chave not in _arquivados:
            return False
        _arquivados.discard(chave)
        return True

    async def esta_arquivada(self, tenant_id: UUID, empresa_cnpj: str) -> bool:
        return (str(tenant_id), empresa_cnpj) in _arquivados

    async def listar_cnpjs_arquivados(self, tenant_id: UUID) -> frozenset[str]:
        tid = str(tenant_id)
        return frozenset(cnpj for t, cnpj in _arquivados if t == tid)
