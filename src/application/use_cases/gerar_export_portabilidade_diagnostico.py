"""
Caso de uso: gerar pacote de portabilidade (JSON + opcional PDF com anexo).

Camada: Application
Base: ADR-012 §4 — exige solicitação LGPD tipo ``portabilidade`` com status ``deferida``.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.application.ports.lgpd_titular_solicitacao_port import (
    LgpdTitularSolicitacaoPort,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.domain.entities.diagnostico import StatusDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.services.diagnostico_export_v1 import montar_payload_export_v1


@dataclass(frozen=True)
class ComandoGerarExportPortabilidadeDiagnostico:
    """Parâmetros para export portável."""

    tenant_id: UUID
    diagnostico_id: UUID
    solicitacao_id: UUID
    gerar_pdf_anexo: bool


@dataclass(frozen=True)
class ResultadoExportPortabilidadeDiagnostico:
    """Pacote serializado."""

    payload: dict[str, Any]
    json_utf8: bytes
    pdf_bytes: bytes | None


class GerarExportPortabilidadeDiagnostico:
    """Orquestra validação de solicitação LGPD + montagem do pacote."""

    def __init__(
        self,
        *,
        diagnostico_repository: DiagnosticoRepository,
        solicitacoes: LgpdTitularSolicitacaoPort,
        validar_payload_export_v1: Callable[[dict[str, Any]], None],
        gerar_pdf_com_anexo_json: Callable[[bytes, str, str], bytes],
    ) -> None:
        self._repo = diagnostico_repository
        self._sol = solicitacoes
        self._validar = validar_payload_export_v1
        self._gerar_pdf = gerar_pdf_com_anexo_json

    async def execute(
        self, comando: ComandoGerarExportPortabilidadeDiagnostico
    ) -> ResultadoExportPortabilidadeDiagnostico:
        sol = await self._sol.buscar_por_id(
            tenant_id=comando.tenant_id,
            solicitacao_id=comando.solicitacao_id,
        )
        if sol is None:
            raise ValueError("Solicitação LGPD não encontrada para este tenant.")
        if sol.diagnostico_id != comando.diagnostico_id:
            raise ValueError("Solicitação não corresponde ao diagnóstico indicado.")
        if sol.tipo != TipoSolicitacaoTitular.PORTABILIDADE:
            raise ValueError("Solicitação deve ser do tipo portabilidade.")
        if sol.status != StatusSolicitacaoTitular.DEFERIDA:
            raise ValueError("Solicitação deve estar deferida para gerar o pacote.")

        diag = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diag is None:
            raise ValueError("Diagnóstico não encontrado.")
        if diag.status != StatusDiagnostico.FINALIZADO:
            raise ValueError("Apenas diagnóstico finalizado pode ser exportado.")
        if not diag.hash_evidencia:
            raise ValueError("Diagnóstico sem hash de evidência — export indisponível.")

        payload = montar_payload_export_v1(diag)
        self._validar(payload)
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        json_utf8 = raw.encode("utf-8")

        pdf_bytes: bytes | None = None
        if comando.gerar_pdf_anexo:
            pdf_bytes = self._gerar_pdf(
                json_utf8,
                str(comando.diagnostico_id),
                str(comando.tenant_id),
            )

        return ResultadoExportPortabilidadeDiagnostico(
            payload=payload,
            json_utf8=json_utf8,
            pdf_bytes=pdf_bytes,
        )
