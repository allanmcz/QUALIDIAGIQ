"""
Caso de uso: mesclar e persistir anotações do quadro de implantação (prazo meta + comentários) com lock otimista.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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
    quadro_implantacao_anotacoes: dict[str, dict[str, Any]]
    versao_esperada: int


class AtualizarQuadroImplantacao:
    """Mescla chaves no mapa ``quadro_implantacao_anotacoes`` e persiste se ``versao_otimista`` coincidir."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoAtualizarQuadroImplantacao) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))
        if not comando.quadro_implantacao_anotacoes:
            raise ValueError(
                "Indique pelo menos uma chave f{i}_a{j} em quadro_implantacao_anotacoes para atualizar."
            )

        existente = getattr(diagnostico, "quadro_implantacao_anotacoes", None) or {}
        mesclado: dict[str, dict[str, Any]] = {
            str(k): dict(v) if isinstance(v, dict) else {} for k, v in existente.items()
        }
        # Mescla por chave (não substitui o objeto inteiro) para PATCH parcial não apagar
        # ``descricao_personalizada`` ou outros campos futuros quando só prazo/comentários forem enviados.
        for chave, parcial in comando.quadro_implantacao_anotacoes.items():
            ck = str(chave).strip()
            anterior = mesclado.get(ck, {})
            if not isinstance(anterior, dict):
                anterior = {}
            if not isinstance(parcial, dict):
                parcial = {}
            mesclado[ck] = {**anterior, **parcial}

        try:
            diagnostico.definir_quadro_implantacao_anotacoes(mesclado)
        except DiagnosticoNaoFinalizavelError as e:
            raise ValueError(str(e)) from e

        atualizado = await self._repo.atualizar_quadro_implantacao_com_versao(
            comando.diagnostico_id,
            comando.tenant_id,
            mesclado,
            comando.versao_esperada,
        )
        if atualizado is None:
            raise ConflitoVersaoOtimistaError(
                f"Versão otimista esperada {comando.versao_esperada} não aplicada."
            )
        return atualizado
