"""
Caso de uso: anexar URL do PDF com lock otimista (If-Match ↔ versao_otimista).

Camada: Application
Depende de: domain, port ``DiagnosticoRepository`` e ``DiagnosticoMutacaoAuditPort``.

Base normativa:
    - Previsibilidade e consistência em operações concorrentes — LC 214/2025
    - Evidências auditáveis — ABNT NBR 17301:2026
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.ports.diagnostico_mutacao_audit_port import (
    DiagnosticoMutacaoAuditPort,
    TipoMutacaoDiagnostico,
)
from src.domain.entities.diagnostico import Diagnostico, DiagnosticoNaoFinalizavelError

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ComandoAnexarRelatorioOtimista:
    """Entrada do PATCH de relatório."""

    tenant_id: UUID
    diagnostico_id: UUID
    relatorio_pdf_url: str
    versao_esperada: int
    actor_user_id: UUID | None = None


class AnexarRelatorioOtimista:
    """Anexa `relatorio_pdf_url` somente se a versão otimista bater com o banco."""

    def __init__(
        self,
        repo: DiagnosticoRepository,
        mutacao_audit: DiagnosticoMutacaoAuditPort,
    ) -> None:
        self._repo = repo
        self._mutacao_audit = mutacao_audit

    async def execute(self, comando: ComandoAnexarRelatorioOtimista) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))

        try:
            diagnostico.anexar_relatorio(comando.relatorio_pdf_url)
        except DiagnosticoNaoFinalizavelError:
            raise

        atualizado = await self._repo.atualizar_relatorio_pdf_com_versao(
            comando.diagnostico_id,
            comando.tenant_id,
            comando.relatorio_pdf_url,
            comando.versao_esperada,
        )
        if atualizado is None:
            raise ConflitoVersaoOtimistaError(
                f"Versão otimista esperada {comando.versao_esperada} não aplicada."
            )
        try:
            await self._mutacao_audit.registrar(
                tenant_id=comando.tenant_id,
                diagnostico_id=comando.diagnostico_id,
                tipo=TipoMutacaoDiagnostico.RELATORIO_PDF,
                payload={"relatorio_pdf_url": comando.relatorio_pdf_url},
                actor_user_id=comando.actor_user_id,
                versao_otimista_antes=comando.versao_esperada,
                versao_otimista_apos=atualizado.versao_otimista,
            )
        except Exception as exc:
            logger.warning(
                "diagnostico_mutacao_audit_falhou",
                tipo="relatorio_pdf",
                diagnostico_id=str(comando.diagnostico_id),
                erro=str(exc),
                exc_info=True,
            )
        return atualizado
