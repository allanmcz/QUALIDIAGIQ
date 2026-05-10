"""
Caso de uso: mesclar e persistir anotações do quadro de implantação (prazo meta + comentários) com lock otimista.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

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
class ComandoAtualizarQuadroImplantacao:
    """Entrada do PATCH quadro de implantação."""

    tenant_id: UUID
    diagnostico_id: UUID
    quadro_implantacao_anotacoes: dict[str, dict[str, Any]]
    versao_esperada: int
    actor_user_id: UUID | None = None


class AtualizarQuadroImplantacao:
    """Mescla chaves no mapa ``quadro_implantacao_anotacoes`` e persiste se ``versao_otimista`` coincidir."""

    def __init__(
        self,
        repo: DiagnosticoRepository,
        mutacao_audit: DiagnosticoMutacaoAuditPort,
    ) -> None:
        self._repo = repo
        self._mutacao_audit = mutacao_audit

    async def execute(self, comando: ComandoAtualizarQuadroImplantacao) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))
        if not comando.quadro_implantacao_anotacoes:
            raise ValueError(
                "Indique pelo menos uma chave (UUID da ação ou f0_a0) em quadro_implantacao_anotacoes."
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
            if not isinstance(anterior, dict):  # pragma: no cover — defesa contra JSONB legado
                anterior = {}
            if not isinstance(parcial, dict):
                parcial = {}
            mesclado[ck] = {**anterior, **parcial}

        try:
            diagnostico.definir_quadro_implantacao_anotacoes(mesclado)
        except DiagnosticoNaoFinalizavelError:
            raise

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
        try:
            await self._mutacao_audit.registrar(
                tenant_id=comando.tenant_id,
                diagnostico_id=comando.diagnostico_id,
                tipo=TipoMutacaoDiagnostico.QUADRO_IMPLANTACAO,
                payload={
                    "chaves_enviadas": sorted(comando.quadro_implantacao_anotacoes.keys()),
                    "quadro_implantacao_anotacoes": mesclado,
                },
                actor_user_id=comando.actor_user_id,
                versao_otimista_antes=comando.versao_esperada,
                versao_otimista_apos=atualizado.versao_otimista,
            )
        except Exception as exc:
            logger.warning(
                "diagnostico_mutacao_audit_falhou",
                tipo="quadro_implantacao",
                diagnostico_id=str(comando.diagnostico_id),
                erro=str(exc),
                exc_info=True,
            )
        return atualizado
