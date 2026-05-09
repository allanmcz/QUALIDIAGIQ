"""
Port — persistência de consultas CNPJ (cache TTL triplo) e merge em diagnóstico.

Camada: Application
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from src.domain.entities.diagnostico import EmpresaInfo

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class CnpjConsultaRepositoryPort(ABC):
    """Contrato para Postgres (SQL direto); Supabase REST ficaria para outro adapter."""

    @abstractmethod
    def buscar_por_idempotencia(
        self, tenant_id: UUID, idempotency_key: str
    ) -> dict[str, Any] | None:
        """Linha ``cnpj_consultas`` já gravada para a mesma chave idempotente."""

    @abstractmethod
    def buscar_ultimo_cache_valido_triplo_ttl(
        self, tenant_id: UUID, cnpj: str
    ) -> dict[str, Any] | None:
        """Última consulta cujo triple-expiry ainda cobre cadastro, qualificação e situação."""

    @abstractmethod
    def inserir_consulta(
        self,
        *,
        tenant_id: UUID,
        idempotency_key: str,
        cnpj: str,
        diagnostico_id: UUID | None,
        payload_bruto: dict[str, Any],
        payload_canonico: dict[str, Any],
        payload_hash: str,
        fonte: str,
        consultado_em: datetime,
        expira_cadastral_at: datetime,
        expira_qualificacao_at: datetime,
        expira_situacao_at: datetime,
        latencia_ms: int | None,
        http_status: int | None,
        trace_id: str | None,
    ) -> UUID:
        """Persiste snapshot; ``fonte`` ∈ {brasil_api, minha_receita}."""

    @abstractmethod
    def atualizar_empresa_diagnostico_em_andamento(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        nova_empresa: EmpresaInfo,
        historico: list[tuple[str, str | None, str]],
        cnpj_consulta_id: UUID | None,
    ) -> None:
        """
        Atualiza colunas empresa_* somente se ``status = em_andamento``.

        Raises:
            ValueError: diagnóstico inexistente, tenant divergente ou não está em andamento.
        """
