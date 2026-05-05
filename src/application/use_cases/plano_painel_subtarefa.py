"""
Casos de uso — subtarefas do plano de ação materializado.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from src.domain.repositories.diagnostico_repository import DiagnosticoRepository


@dataclass(frozen=True)
class ComandoCriarSubtarefaPlanoDiagnostico:
    """Entrada para criar subtarefa ligada a ``plano_acao_id``."""

    tenant_id: UUID
    diagnostico_id: UUID
    plano_acao_id: UUID
    titulo: str
    ordem: int = 0


@dataclass(frozen=True)
class ComandoAtualizarSubtarefaPlanoDiagnostico:
    """Atualização parcial de subtarefa (campos None são ignorados)."""

    tenant_id: UUID
    diagnostico_id: UUID
    subtarefa_id: UUID
    titulo: str | None = None
    status: str | None = None
    prazo: date | None = None
    comentarios: str | None = None
    ordem: int | None = None


class CriarSubtarefaPlanoDiagnostico:
    """Persiste subtarefa normalizada (D5)."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoCriarSubtarefaPlanoDiagnostico) -> dict[str, Any]:
        t = comando.titulo.strip()
        if not t:
            raise ValueError("titulo é obrigatório.")
        return await self._repo.inserir_subtarefa_plano(
            comando.tenant_id,
            comando.diagnostico_id,
            comando.plano_acao_id,
            t,
            comando.ordem,
        )


class AtualizarSubtarefaPlanoDiagnostico:
    """Atualiza campos opcionais da subtarefa."""

    def __init__(self, repo: DiagnosticoRepository) -> None:
        self._repo = repo

    async def execute(self, comando: ComandoAtualizarSubtarefaPlanoDiagnostico) -> dict[str, Any]:
        out = await self._repo.atualizar_subtarefa_plano(
            comando.tenant_id,
            comando.diagnostico_id,
            comando.subtarefa_id,
            titulo=comando.titulo,
            status=comando.status,
            prazo=comando.prazo,
            comentarios=comando.comentarios,
            ordem=comando.ordem,
        )
        if out is None:
            raise ValueError("Subtarefa não encontrada para este diagnóstico/tenant.")
        return out
