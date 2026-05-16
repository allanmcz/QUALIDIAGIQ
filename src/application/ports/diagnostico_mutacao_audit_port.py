"""
Port de persistência do log append-only de mutações pós-finalização (M12, quadro, PDF).

Camada: Application (interface — Dependency Inversion Principle)

Implementações: ``PostgresDiagnosticoMutacaoAuditAdapter`` (DSN síncrono) e No-op quando
não há Postgres (ex.: Supabase PostgREST ou CI em memória).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID


class TipoMutacaoDiagnostico(StrEnum):
    """Tipo de evento gravado em ``diagnostico_mutacao_audit``."""

    M12_LIKERT = "m12_likert"
    QUADRO_IMPLANTACAO = "quadro_implantacao"
    RELATORIO_PDF = "relatorio_pdf"
    PAINEL_ESTADO_CICLO = "painel_estado_ciclo"


class DiagnosticoMutacaoAuditPort(ABC):
    """Contrato para registrar uma linha de auditoria (INSERT apenas no adaptador Postgres)."""

    @abstractmethod
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
        """
        Persiste um evento de mutação permitida após ``finalizado``.

        Args:
            tenant_id: Tenant do JWT.
            diagnostico_id: ID do diagnóstico alterado.
            tipo: Classificação do PATCH.
            payload: Dados versionados do estado relevante (JSON serializável).
            actor_user_id: Claim ``sub`` do JWT, se houver.
            versao_otimista_antes: Valor esperado no If-Match (lock otimista).
            versao_otimista_apos: Valor retornado após o UPDATE bem-sucedido.

        Raises:
            Exception: Erros de I/O do adaptador Postgres (o caso de uso pode registrar log e seguir).
        """
        ...
