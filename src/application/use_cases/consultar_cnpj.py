"""
Use case — consulta CNPJ autenticada com cache TTL triplo e merge opcional em diagnóstico.

Camada: Application
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.application.ports.cnpj_consulta_repository_port import CnpjConsultaRepositoryPort
from src.application.services.cnpj_consulta_mapeamento import mesclar_empresa_com_sugestao_cnpj
from src.application.services.cnpj_consulta_service import (
    CnpjConsultaService,
    ConsultaCnpjMaterializada,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True)
class ComandoConsultarCnpj:
    """Entrada para POST ``/referencia/cnpj/consulta_cnpj``."""

    tenant_id: UUID
    cnpj_14: str
    idempotency_key: str
    force_refresh: bool = False
    aplicar_no_diagnostico_id: UUID | None = None
    trace_id: str | None = None


class ConsultarCnpjUseCase:
    """Orquestra ``CnpjConsultaService`` + merge em ``diagnosticos`` (somente ``em_andamento``)."""

    def __init__(
        self,
        *,
        service: CnpjConsultaService,
        cnpj_repo: CnpjConsultaRepositoryPort,
        diagnostico_repo: DiagnosticoRepository,
    ) -> None:
        self._service = service
        self._cnpj_repo = cnpj_repo
        self._diagnostico_repo = diagnostico_repo

    async def executar_e_materializar(
        self, comando: ComandoConsultarCnpj
    ) -> tuple[ConsultaCnpjMaterializada, bool]:
        """
        Materializa consulta e opcionalmente aplica merge no diagnóstico em andamento.

        Returns:
            Tupla ``(materializada, aplicado_no_diagnostico)``.
        """
        mat = await self._service.materializar_consulta(
            tenant_id=comando.tenant_id,
            cnpj_14=comando.cnpj_14,
            idempotency_key=comando.idempotency_key,
            force_refresh=comando.force_refresh,
            diagnostico_id=comando.aplicar_no_diagnostico_id,
            trace_id=comando.trace_id,
        )
        aplicado = False
        if comando.aplicar_no_diagnostico_id is not None:
            d = await self._diagnostico_repo.buscar_por_id(
                comando.aplicar_no_diagnostico_id, comando.tenant_id
            )
            if d is None:
                raise ValueError("Diagnóstico não encontrado para o tenant atual.")
            nova, hist = mesclar_empresa_com_sugestao_cnpj(
                d.empresa,
                mat.payload_canonico,
                cnpj_consulta_14=mat.cnpj_14,
            )
            if hist:
                await asyncio.to_thread(
                    self._cnpj_repo.atualizar_empresa_diagnostico_em_andamento,
                    tenant_id=comando.tenant_id,
                    diagnostico_id=comando.aplicar_no_diagnostico_id,
                    nova_empresa=nova,
                    historico=hist,
                    cnpj_consulta_id=mat.consulta_id,
                )
                aplicado = True
        return mat, aplicado
