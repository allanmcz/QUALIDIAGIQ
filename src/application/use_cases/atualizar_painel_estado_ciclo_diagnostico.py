"""
Caso de uso: atualizar o estado operacional da consultoria no grid do painel (campo persistente).

Camada: Application
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
from src.domain.entities.diagnostico import Diagnostico, PainelEstadoCicloDiagnostico

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ComandoAtualizarPainelEstadoCicloDiagnostico:
    tenant_id: UUID
    diagnostico_id: UUID
    painel_estado_ciclo: PainelEstadoCicloDiagnostico
    versao_esperada: int
    actor_user_id: UUID | None = None


class AtualizarPainelEstadoCicloDiagnostico:
    """Persiste ``painel_estado_ciclo`` somente se ``versao_otimista`` coincidir."""

    def __init__(
        self,
        repo: DiagnosticoRepository,
        mutacao_audit: DiagnosticoMutacaoAuditPort,
    ) -> None:
        self._repo = repo
        self._mutacao_audit = mutacao_audit

    async def execute(self, comando: ComandoAtualizarPainelEstadoCicloDiagnostico) -> Diagnostico:
        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise DiagnosticoNaoEncontradoError(str(comando.diagnostico_id))

        diagnostico.definir_painel_estado_ciclo(comando.painel_estado_ciclo)

        atualizado = await self._repo.atualizar_painel_estado_ciclo_com_versao(
            comando.diagnostico_id,
            comando.tenant_id,
            comando.painel_estado_ciclo.value,
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
                tipo=TipoMutacaoDiagnostico.PAINEL_ESTADO_CICLO,
                payload={"painel_estado_ciclo": comando.painel_estado_ciclo.value},
                actor_user_id=comando.actor_user_id,
                versao_otimista_antes=comando.versao_esperada,
                versao_otimista_apos=atualizado.versao_otimista,
            )
        except Exception as exc:
            logger.warning(
                "diagnostico_mutacao_audit_falhou",
                tipo="painel_estado_ciclo",
                diagnostico_id=str(comando.diagnostico_id),
                erro=str(exc),
                exc_info=True,
            )
        return atualizado
