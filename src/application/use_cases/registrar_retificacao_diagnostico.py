"""
Caso de uso: registar retificação append-only (ADR-012 §5).

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.application.ports.diagnostico_retificacao_port import (
    DiagnosticoRetificacaoPort,
    DiagnosticoRetificacaoRegisto,
)
from src.domain.entities.diagnostico import StatusDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.services.diagnostico_retificacao_hash import (
    calcular_hash_retificacao_sha256,
    montar_canonical_retificacao,
)


@dataclass(frozen=True)
class ComandoRegistrarRetificacaoDiagnostico:
    """Entrada para nova retificação na cadeia."""

    tenant_id: UUID
    actor_user_id: UUID
    diagnostico_original_id: UUID
    motivo_retificacao: str
    payload_retificacao: dict[str, Any]


class RegistrarRetificacaoDiagnostico:
    """Valida WORM + hash do original e persiste retificação."""

    def __init__(
        self,
        *,
        diagnostico_repository: DiagnosticoRepository,
        retificacao: DiagnosticoRetificacaoPort,
    ) -> None:
        self._repo = diagnostico_repository
        self._ret = retificacao

    async def execute(
        self, comando: ComandoRegistrarRetificacaoDiagnostico
    ) -> DiagnosticoRetificacaoRegisto:
        d = await self._repo.buscar_por_id(
            comando.diagnostico_original_id,
            comando.tenant_id,
        )
        if d is None:
            raise ValueError("Diagnóstico não encontrado.")
        if d.status != StatusDiagnostico.FINALIZADO:
            raise ValueError("Só é possível retificar diagnóstico finalizado.")
        if not d.hash_evidencia:
            raise ValueError("Diagnóstico sem hash de evidência — retificação indisponível.")

        rid = uuid4()
        agora = datetime.now(UTC)
        canon = montar_canonical_retificacao(
            tenant_id=comando.tenant_id,
            diagnostico_original_id=comando.diagnostico_original_id,
            hash_diagnostico_original_sha256=d.hash_evidencia,
            motivo_retificacao=comando.motivo_retificacao,
            payload_retificacao=comando.payload_retificacao,
            retificacao_id=rid,
            criado_em=agora,
            actor_user_id=comando.actor_user_id,
        )
        h_ret = calcular_hash_retificacao_sha256(canon)

        return await self._ret.inserir(
            retificacao_id=rid,
            tenant_id=comando.tenant_id,
            diagnostico_original_id=comando.diagnostico_original_id,
            hash_diagnostico_original_sha256=d.hash_evidencia.lower(),
            motivo_retificacao=comando.motivo_retificacao.strip(),
            payload_retificacao=comando.payload_retificacao,
            hash_retificacao_sha256=h_ret,
            actor_user_id=comando.actor_user_id,
        )
