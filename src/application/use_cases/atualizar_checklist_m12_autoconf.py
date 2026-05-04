"""
Caso de uso: persistir autoconf ABNT M12 (10 x Likert 1-5) com lock otimista.

Camada: Application
Depende apenas de: domain + port DiagnosticoRepository

Base normativa:
    - ABNT NBR 17301:2026 — autoconferência / evidências operacionais
    - LC 214/2025 — previsibilidade e consistência em operações concorrentes
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
class ComandoAtualizarChecklistM12Autoconf:
    """Entrada do PATCH M12."""

    tenant_id: UUID
    diagnostico_id: UUID
    checklist_m12_autoconf: list[int]
    versao_esperada: int


class AtualizarChecklistM12Autoconf:
    """Grava `checklist_m12_estado` somente se `versao_otimista` coincidir."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoAtualizarChecklistM12Autoconf) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))

        try:
            diagnostico.definir_checklist_m12_autoconf(comando.checklist_m12_autoconf)
        except DiagnosticoNaoFinalizavelError as e:
            raise ValueError(str(e)) from e

        atualizado = await self._repo.atualizar_checklist_m12_com_versao(
            comando.diagnostico_id,
            comando.tenant_id,
            comando.checklist_m12_autoconf,
            comando.versao_esperada,
        )
        if atualizado is None:
            raise ConflitoVersaoOtimistaError(
                f"Versão otimista esperada {comando.versao_esperada} não aplicada."
            )
        return atualizado
