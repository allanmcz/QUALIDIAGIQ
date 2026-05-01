"""
Caso de uso: anexar URL do PDF com lock otimista (If-Match ↔ versao_otimista).

Camada: Application
Depende apenas de: domain + port DiagnosticoRepository

Base normativa:
    - Previsibilidade e consistência em operações concorrentes — LC 214/2025
    - Evidências auditáveis — ABNT NBR 17301:2026
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.domain.entities.diagnostico import Diagnostico, DiagnosticoNaoFinalizavelError

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository


@dataclass(frozen=True)
class ComandoAnexarRelatorioOtimista:
    """Entrada do PATCH de relatório."""

    tenant_id: UUID
    diagnostico_id: UUID
    relatorio_pdf_url: str
    versao_esperada: int


class AnexarRelatorioOtimista:
    """Anexa `relatorio_pdf_url` somente se a versão otimista bater com o banco."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoAnexarRelatorioOtimista) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))

        try:
            diagnostico.anexar_relatorio(comando.relatorio_pdf_url)
        except DiagnosticoNaoFinalizavelError as e:
            raise ValueError(str(e)) from e

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
        return atualizado
