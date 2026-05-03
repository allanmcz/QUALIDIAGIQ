"""
Caso de uso: persistir anotações do quadro de implantação (comentário + prazo meta) com lock otimista.

Camada: Application
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
class ComandoAtualizarQuadroImplantacao:
    """Entrada do PATCH quadro de implantação."""

    tenant_id: UUID
    diagnostico_id: UUID
    quadro_implantacao_anotacoes: dict[str, dict[str, str]]
    versao_esperada: int


class AtualizarQuadroImplantacao:
    """Grava ``quadro_implantacao_anotacoes`` somente se ``versao_otimista`` coincidir."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoAtualizarQuadroImplantacao) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))

        try:
            diagnostico.definir_quadro_implantacao_anotacoes(comando.quadro_implantacao_anotacoes)
        except DiagnosticoNaoFinalizavelError as e:
            raise ValueError(str(e)) from e

        atualizado = await self._repo.atualizar_quadro_implantacao_com_versao(
            comando.diagnostico_id,
            comando.tenant_id,
            comando.quadro_implantacao_anotacoes,
            comando.versao_esperada,
        )
        if atualizado is None:
            raise ConflitoVersaoOtimistaError(
                f"Versão otimista esperada {comando.versao_esperada} não aplicada."
            )
        return atualizado
