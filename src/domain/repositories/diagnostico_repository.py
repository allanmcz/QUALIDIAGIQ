"""
Port (interface) de persistência de Diagnóstico.

Camada: Domain (interface — Dependency Inversion Principle)

Implementação concreta vive em:
    ``src/infrastructure/repositories/postgres_diagnostico_repository.py`` (quando há DSN) ou
    ``src/infrastructure/repositories/supabase_diagnostico_repository.py`` (PostgREST).

Princípio: domain define o contrato, infrastructure implementa.
Isso permite trocar Supabase → PostgreSQL puro → MongoDB sem tocar nas regras de negócio.

Analogia para o Allan:
    É como definir uma interface no Delphi (`type IDiagnosticoRepo = interface`)
    que múltiplas implementações concretas podem honrar (Oracle, FireDAC, ZeosLib...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from uuid import UUID

from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import ScoreCompleto


class DiagnosticoRepository(ABC):
    """Port de persistência da entidade Diagnóstico."""

    @abstractmethod
    async def salvar(self, diagnostico: Diagnostico) -> None:
        """
        Persiste o agregado completo (insert ou update conforme existência).

        Idempotente em relação a `diagnostico.id` (UUID).
        """
        ...

    @abstractmethod
    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        """
        Busca diagnóstico por ID, **respeitando isolamento multi-tenant** (RLS).

        Returns:
            Diagnóstico se encontrado; None caso contrário.
        """
        ...

    @abstractmethod
    async def listar_por_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Diagnostico]:
        """Lista diagnósticos de um tenant, paginado."""
        ...

    @abstractmethod
    async def atualizar_relatorio_pdf_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        relatorio_pdf_url: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        """
        Atualiza apenas a URL do PDF com lock otimista (`versao_otimista`).

        Retorna:
            Diagnóstico atualizado se uma linha foi afetada; None se a versão não coincidir.
        """
        ...

    @abstractmethod
    async def atualizar_checklist_m12_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        checklist_m12_estado: list[int],
        versao_esperada: int,
    ) -> Diagnostico | None:
        """
        Persiste os 10 valores Likert (1-5) M12 com lock otimista (incrementa `versao_otimista`).

        Retorna:
            Diagnóstico atualizado se o UPDATE afetou uma linha; None em conflito de versão.
        """
        ...

    @abstractmethod
    async def atualizar_quadro_implantacao_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        quadro_implantacao_anotacoes: dict[str, dict[str, Any]],
        versao_esperada: int,
    ) -> Diagnostico | None:
        """
        Persiste JSONB do quadro de implantação (comentários e prazos meta) com lock otimista.

        Retorna:
            Diagnóstico atualizado se o UPDATE afetou uma linha; None em conflito de versão.
        """
        ...

    @abstractmethod
    async def salvar_e_materializar_plano_painel(
        self,
        diagnostico: Diagnostico,
        score_completo: ScoreCompleto,
        *,
        historico_campos_empresa_cnpj: list[tuple[str, str | None, str]] | None = None,
        cnpj_consulta_id: UUID | None = None,
    ) -> PlanoPainelSerializado:
        """
        Persiste o diagnóstico e materializa plano/matriz/cronograma na mesma transação (Postgres).

        Em adaptadores sem transação atómica (ex.: PostgREST), aplica a sequência mais próxima possível.

        Args:
            historico_campos_empresa_cnpj: Trilha append-only de merge CNPJ antes da evidência WORM.
            cnpj_consulta_id: FK opcional para ``cnpj_consultas``.

        Raises:
            RuntimeError: falha de persistência ao materializar (fluxo novo não deve concluir «à meio»).
        """
        ...

    @abstractmethod
    async def buscar_plano_painel_serializado(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        """Lê snapshot materializado; None se ainda não existir (legado antes do backfill)."""
        ...

    @abstractmethod
    async def materializar_plano_painel_idempotente_backfill(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        """
        Materializa ``versao_plano = 1`` se o diagnóstico estiver finalizado e ainda não houver linhas.

        Returns:
            Snapshot gravado, ou None se nada foi feito (já materializado ou dados insuficientes).
        """
        ...

    @abstractmethod
    async def inserir_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        titulo: str,
        ordem: int = 0,
    ) -> dict[str, Any]:
        """Insere subtarefa ligada a uma ação materializada (tenant isolado por RLS)."""
        ...

    @abstractmethod
    async def atualizar_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        subtarefa_id: UUID,
        *,
        titulo: str | None = None,
        status: str | None = None,
        prazo: date | None = None,
        comentarios: str | None = None,
        ordem: int | None = None,
    ) -> dict[str, Any] | None:
        """Atualiza campos opcionais da subtarefa; None se não existir no tenant."""
        ...
