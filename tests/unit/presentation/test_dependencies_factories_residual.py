"""Factories restantes em ``dependencies.py`` (ramos Postgres e ``Depends`` triviais).

Objetivo: cobrir linhas que o relatório marca como ``Miss`` quando só existiam fluxos CI/Supabase
ou erros HTTP testados isoladamente.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.application.ports.lead_diagnostico_vinculo_port import LeadDiagnosticoVinculoPort
from src.application.use_cases.anexar_relatorio_otimista import AnexarRelatorioOtimista
from src.application.use_cases.atualizar_checklist_m12_autoconf import (
    AtualizarChecklistM12Autoconf,
)
from src.application.use_cases.atualizar_quadro_implantacao import AtualizarQuadroImplantacao
from src.application.use_cases.atualizar_status_solicitacao_titular_lgpd import (
    AtualizarStatusSolicitacaoTitularLgpd,
)
from src.application.use_cases.consultar_cnpj import ConsultarCnpjUseCase
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ExecutarAnonimizacaoRespondenteLgpd,
)
from src.application.use_cases.executar_eliminacao_diagnostico_lgpd import (
    ExecutarEliminacaoDiagnosticoLgpd,
)
from src.application.use_cases.plano_painel_subtarefa import (
    AtualizarSubtarefaPlanoDiagnostico,
    CriarSubtarefaPlanoDiagnostico,
)
from src.application.use_cases.registrar_solicitacao_titular_lgpd import (
    RegistrarSolicitacaoTitularLgpd,
)
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    VincularDiagnosticosLeadSelfService,
)
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.config.settings import get_settings
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)
from src.presentation.api import dependencies as deps


@pytest.fixture(autouse=True)
def _limpar_settings() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_self_service_diagnostico_claims_token_jwt_invalido_401(monkeypatch) -> None:
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="jwt_invalido_qualquer")

    def _boom_decode(_token: str, _secret: str, algorithms=None, **kwargs):  # type: ignore[no-untyped-def]
        raise jwt.InvalidTokenError()

    monkeypatch.setattr(deps.jwt, "decode", _boom_decode)

    from src.presentation.api.dependencies import get_self_service_diagnostico_claims

    with pytest.raises(HTTPException) as ei:
        await get_self_service_diagnostico_claims(creds)
    assert ei.value.status_code == 401


def test_get_diagnostico_repository_postgres_quando_database_url(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/qdi_dummy")
    get_settings.cache_clear()
    try:
        repo = deps.get_diagnostico_repository()
        assert isinstance(repo, PostgresDiagnosticoRepository)
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_lead_diagnostico_vinculo_postgres(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/qdi_dummy")
    get_settings.cache_clear()
    try:
        port = deps.get_lead_diagnostico_vinculo_port()
        assert type(port).__name__ == "PostgresLeadDiagnosticoVinculoAdapter"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_lgpd_titular_adapter_com_dsn(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/x")
    get_settings.cache_clear()
    try:
        port = deps.get_lgpd_titular_solicitacao_port()
        assert type(port).__name__ == "PostgresLgpdTitularSolicitacaoAdapter"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_lgpd_executor_com_dsn(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/y")
    get_settings.cache_clear()
    try:
        ex = deps.get_lgpd_anonimizacao_executor_port()
        assert type(ex).__name__ == "PostgresLgpdAnonimizacaoExecutorAdapter"
        ex2 = deps.get_lgpd_eliminacao_executor_port()
        assert type(ex2).__name__ == "PostgresLgpdEliminacaoExecutorAdapter"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_diagnostico_mutacao_audit_adapter_postgres(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:1/z")
    get_settings.cache_clear()
    try:
        p = deps.get_diagnostico_mutacao_audit_port()
        assert type(p).__name__ == "PostgresDiagnosticoMutacaoAuditAdapter"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_vincular_leads_use_case() -> None:
    vinc = MagicMock(spec=LeadDiagnosticoVinculoPort)
    uc = deps.get_vincular_diagnosticos_lead_self_service_use_case(vinc)
    assert isinstance(uc, VincularDiagnosticosLeadSelfService)


def test_get_anexar_relatorio_otimista() -> None:
    r = MagicMock()
    audit = MagicMock()
    uc = deps.get_anexar_relatorio_otimista_use_case(r, audit)
    assert isinstance(uc, AnexarRelatorioOtimista)


def test_get_atualizar_checklist_m12() -> None:
    r = MagicMock()
    audit = MagicMock()
    uc = deps.get_atualizar_checklist_m12_autoconf_use_case(r, audit)
    assert isinstance(uc, AtualizarChecklistM12Autoconf)


def test_get_atualizar_quadro_implantacao_factory() -> None:
    r = MagicMock()
    audit = MagicMock()
    uc = deps.get_atualizar_quadro_implantacao_use_case(r, audit)
    assert isinstance(uc, AtualizarQuadroImplantacao)


def test_factories_plano_painel_subtarefas() -> None:
    r = MagicMock()
    uc1 = deps.get_criar_subtarefa_plano_diagnostico_use_case(r)
    assert isinstance(uc1, CriarSubtarefaPlanoDiagnostico)
    uc2 = deps.get_atualizar_subtarefa_plano_diagnostico_use_case(r)
    assert isinstance(uc2, AtualizarSubtarefaPlanoDiagnostico)


def test_get_registrar_solicitacao_titular_lgpd() -> None:
    port = MagicMock()
    uc = deps.get_registrar_solicitacao_titular_lgpd_use_case(port)
    assert isinstance(uc, RegistrarSolicitacaoTitularLgpd)


def test_get_listar_e_atualizar_status_solicitacao_lgpd() -> None:
    port = MagicMock()
    listar_uc = deps.get_listar_solicitacao_titular_lgpd_use_case(port)
    assert type(listar_uc).__name__ == "ListarSolicitacaoTitularLgpd"
    ua = deps.get_atualizar_status_solicitacao_titular_lgpd_use_case(port)
    assert isinstance(ua, AtualizarStatusSolicitacaoTitularLgpd)


def test_get_executar_anonimizacao_factory() -> None:
    solicit = MagicMock()
    exe = MagicMock()
    uc = deps.get_executar_anonimizacao_respondente_lgpd_use_case(solicit, exe)
    assert isinstance(uc, ExecutarAnonimizacaoRespondenteLgpd)


def test_get_executar_eliminacao_factory() -> None:
    solicit = MagicMock()
    exe = MagicMock()
    uc = deps.get_executar_eliminacao_diagnostico_lgpd_use_case(solicit, exe)
    assert isinstance(uc, ExecutarEliminacaoDiagnosticoLgpd)


def test_get_pdf_storage_email_factories(monkeypatch) -> None:
    gen = deps.get_pdf_generator()
    assert isinstance(gen, WeasyPrintPdfGenerator)

    cliente = MagicMock()
    monkeypatch.setattr(deps, "get_supabase_client", lambda: cliente)
    stor = deps.get_storage_service(cliente)
    assert type(stor).__name__ == "SupabaseStorageAdapter"

    mail = deps.get_email_service()
    assert type(mail).__name__ == "SmtpEmailAdapter"


def test_get_consultar_cnpj_use_case_camada_feliz(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://svc:svc@localhost:6543/testcn")
    get_settings.cache_clear()
    diag_repo = MagicMock()
    try:
        with (
            patch.object(deps, "PostgresCnpjConsultaRepository") as ctor_repo,
            patch.object(deps, "CnpjProvedorExternoHttpAdapter") as ctor_prov,
        ):
            ctor_repo.return_value = MagicMock(name="repo_cnpj")
            ctor_prov.return_value = MagicMock(name="provedor_http")
            uc = deps.get_consultar_cnpj_use_case(diag_repo)
        assert isinstance(uc, ConsultarCnpjUseCase)
        assert ctor_repo.call_count >= 2
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()


def test_get_diagnostico_repository_ci_playwright_sem_dsn() -> None:
    """Ramo ``ci_playwright_integrated`` sem ``DATABASE_URL`` (smoke E2E)."""
    fake = MagicMock()
    mock_s = MagicMock()
    mock_s.sync_database_url = None
    mock_s.ci_playwright_integrated = True

    with (
        patch("src.presentation.api.dependencies.get_settings", return_value=mock_s),
        patch("src.presentation.api.dependencies._singleton_ci_playwright_repo", return_value=fake),
    ):
        repo = deps.get_diagnostico_repository()
    assert repo is fake


def test_get_lgpd_anonimizacao_executor_sem_dsn_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(HTTPException) as ei:
            deps.get_lgpd_anonimizacao_executor_port()
        assert ei.value.status_code == 503
        with pytest.raises(HTTPException) as ei2:
            deps.get_lgpd_eliminacao_executor_port()
        assert ei2.value.status_code == 503
    finally:
        get_settings.cache_clear()


def test_cnpj_consulta_service_optional_retorna_servico(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://svc:svc@localhost:6543/opt")
    get_settings.cache_clear()
    try:
        with (
            patch.object(deps, "PostgresCnpjConsultaRepository"),
            patch.object(deps, "CnpjProvedorExternoHttpAdapter"),
        ):
            svc = deps._cnpj_consulta_service_optional()
        assert svc is not None
        assert type(svc).__name__ == "CnpjConsultaService"
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()
