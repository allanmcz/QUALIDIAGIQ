"""
Repositórios e ports de diagnóstico, LGPD, retificação e vínculo lead (DSN vs Supabase vs CI).

Camada: Presentation (FastAPI)

Extraído de ``dependencies.py`` (Onda 2 — fatia repositórios) para reduzir o módulo agregador.
Rotas e testes continuam a importar símbolos reexportados em ``dependencies``.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from src.application.ports.diagnostico_mutacao_audit_port import DiagnosticoMutacaoAuditPort
from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoPort
from src.application.ports.lead_diagnostico_vinculo_port import (
    LeadDiagnosticoVinculoPort,
    NopLeadDiagnosticoVinculoAdapter,
)
from src.application.ports.lgpd_anonimizacao_executor_port import LgpdAnonimizacaoExecutorPort
from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort
from src.application.ports.lgpd_titular_solicitacao_port import LgpdTitularSolicitacaoPort
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.adapters.noop_diagnostico_mutacao_audit_adapter import (
    NoOpDiagnosticoMutacaoAuditAdapter,
)
from src.infrastructure.adapters.postgres_diagnostico_mutacao_audit_adapter import (
    PostgresDiagnosticoMutacaoAuditAdapter,
)
from src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter import (
    PostgresDiagnosticoRetificacaoAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter import (
    PostgresLgpdAnonimizacaoExecutorAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter import (
    PostgresLgpdEliminacaoExecutorAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter import (
    PostgresLgpdTitularSolicitacaoAdapter,
)
from src.infrastructure.config.settings import get_settings
from src.infrastructure.diagnosticos.memoria_lead_diagnostico_vinculo import (
    MemoriaLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo import (
    PostgresLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.repositories.ci_playwright_diagnostico_repository import (
    CiPlaywrightDiagnosticoRepository,
)
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api.deps_auth_supabase import get_supabase_client

_repo_ci_playwright_singleton: CiPlaywrightDiagnosticoRepository | None = None


def reset_ci_playwright_diagnostico_singleton() -> None:
    """Limpa memoização do repositório CI Playwright (testes / recarga controlada)."""
    global _repo_ci_playwright_singleton
    _repo_ci_playwright_singleton = None


def _singleton_ci_playwright_repo() -> CiPlaywrightDiagnosticoRepository:
    global _repo_ci_playwright_singleton
    if _repo_ci_playwright_singleton is None:
        _repo_ci_playwright_singleton = CiPlaywrightDiagnosticoRepository()
    return _repo_ci_playwright_singleton


def get_diagnostico_repository() -> DiagnosticoRepository:
    """Postgres quando há DSN; sem DSN, repositório CI em memória ou Supabase (PostgREST)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresDiagnosticoRepository(dsn_sync=dsn)
    if settings.ci_playwright_integrated:
        return _singleton_ci_playwright_repo()
    return SupabaseDiagnosticoRepository(client=get_supabase_client())


def get_diagnostico_mutacao_audit_port() -> DiagnosticoMutacaoAuditPort:
    """Auditoria append-only em Postgres; no-op sem DSN síncrono (Supabase / memória)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresDiagnosticoMutacaoAuditAdapter(dsn_sync=dsn)
    return NoOpDiagnosticoMutacaoAuditAdapter()


def get_lead_diagnostico_vinculo_port() -> LeadDiagnosticoVinculoPort:
    """
    Reatribuição self-service → tenant da conta na plataforma.

    Com ``DATABASE_URL`` (DSN síncrono), UPDATE via Postgres. Sem DSN e com modo CI Playwright,
    altera o dict in-process (legado sem Postgres).
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresLeadDiagnosticoVinculoAdapter(dsn_sync=dsn)
    if settings.ci_playwright_integrated:
        return MemoriaLeadDiagnosticoVinculoAdapter(
            repo=_singleton_ci_playwright_repo(),
            tenant_self_service=settings.self_service_tenant_id,
        )
    return NopLeadDiagnosticoVinculoAdapter()


def get_lgpd_titular_solicitacao_port() -> LgpdTitularSolicitacaoPort:
    """Port LGPD: exige DSN síncrono para persistir trilha de solicitações do titular."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fluxo LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdTitularSolicitacaoAdapter(dsn_sync=dsn)


def get_lgpd_anonimizacao_executor_port() -> LgpdAnonimizacaoExecutorPort:
    """Executor físico da anonimização — exige Postgres (mesmo DSN das solicitações)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Execução de anonimização LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdAnonimizacaoExecutorAdapter(dsn_sync=dsn)


def get_lgpd_eliminacao_executor_port() -> LgpdEliminacaoExecutorPort:
    """Executor físico da eliminação pré-WORM — exige Postgres (mesmo DSN das solicitações)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Execução de eliminação LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdEliminacaoExecutorAdapter(dsn_sync=dsn)


def get_diagnostico_retificacao_port() -> DiagnosticoRetificacaoPort:
    """Append-only de retificações — mesmo DSN síncrono dos fluxos LGPD."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retificações indisponíveis sem DATABASE_URL síncrono.",
        )
    return PostgresDiagnosticoRetificacaoAdapter(dsn_sync=dsn)
