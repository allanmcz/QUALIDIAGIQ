"""Ramos extras de factories em ``dependencies.py`` (LLM, base normativa, query perfil empresa)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.application.ports.lead_diagnostico_vinculo_port import (
    NopLeadDiagnosticoVinculoAdapter,
)
from src.domain.entities.diagnostico import PorteEmpresa, RegimeTributario, SetorMacro
from src.infrastructure.config.settings import get_settings
from src.infrastructure.diagnosticos.memoria_lead_diagnostico_vinculo import (
    MemoriaLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api import dependencies as deps
from src.presentation.api import deps_auth_supabase


@pytest.fixture(autouse=True)
def _cache() -> None:
    get_settings.cache_clear()
    deps_auth_supabase.reset_supabase_client_singleton()
    yield
    get_settings.cache_clear()
    deps_auth_supabase.reset_supabase_client_singleton()


def test_diagnostico_repository_supabase_sem_dsn_nem_ci_playwright(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("QDI_CI_PLAYWRIGHT_INTEGRATED", raising=False)
    get_settings.cache_clear()
    deps_auth_supabase.reset_supabase_client_singleton()
    fake = MagicMock()

    with patch(
        "src.presentation.api.deps_repositories_core.get_supabase_client", return_value=fake
    ):
        repo = deps.get_diagnostico_repository()
    assert isinstance(repo, SupabaseDiagnosticoRepository)


def test_get_consultar_cnpj_use_case_sem_dsn_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    fake_repo_diag = MagicMock()
    with pytest.raises(HTTPException) as ei:
        deps.get_consultar_cnpj_use_case(repo_diag=fake_repo_diag)
    assert ei.value.status_code == 503


def test_get_buscar_cnae_subclasses_sem_dsn_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as ei:
        deps.get_buscar_cnae_subclasses_use_case()
    assert ei.value.status_code == 503


def test_get_lgpd_titular_port_sem_dsn_503(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    with pytest.raises(HTTPException) as ei:
        deps.get_lgpd_titular_solicitacao_port()
    assert ei.value.status_code == 503


def test_build_base_normativa_pgvector_quando_dsn_e_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@127.0.0.1:1/db")

    fk = MagicMock()
    fk.get_secret_value.return_value = "sk-test-openai-xxxx"

    m = MagicMock()
    m.sync_database_url = "postgresql://x:y@127.0.0.1:1/db"
    m.openai_api_key = fk
    m.openai_embedding_model = "text-embedding-3-small"

    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=m):
        port = deps.build_base_normativa_port()
    assert type(port).__name__ == "PgvectorBaseNormativaAdapter"


def test_get_llm_http_ollama_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_default_tier = "local"
    mock_s.llm_backend = "http_ollama"
    fk = MagicMock()
    fk.get_secret_value.return_value = ""
    mock_s.anthropic_api_key = fk
    mock_s.anthropic_model = "ignored"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "mistral"
    mock_s.ollama_timeout_seconds = 12.0
    mock_s.qdi_rag_similarity_threshold = "0.2"
    mock_s.sync_database_url = None
    mock_s.openai_api_key = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service()
    assert type(svc).__name__ == "OllamaLlmAdapter"


def test_get_llm_anthropic_com_chave_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_default_tier = "premium"
    mock_s.llm_backend = "anthropic"
    fk = MagicMock()
    fk.get_secret_value.return_value = "sk-ant-chave-real"
    mock_s.anthropic_api_key = fk
    mock_s.anthropic_model = "claude-3-haiku-latest"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "fallback"
    mock_s.ollama_timeout_seconds = 20.0
    mock_s.qdi_rag_similarity_threshold = "0.21"
    mock_s.sync_database_url = None
    mock_s.openai_api_key = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service()
    assert type(svc).__name__ == "AnthropicLlmAdapter"


def test_get_llm_anthropic_sem_chave_fallback_langgraph() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_default_tier = "standard"
    mock_s.llm_backend = "anthropic"
    fk = MagicMock()
    fk.get_secret_value.return_value = "   "
    mock_s.anthropic_api_key = fk
    mock_s.anthropic_model = "x"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "m"
    mock_s.ollama_timeout_seconds = 9.0
    mock_s.qdi_rag_similarity_threshold = "0.13"
    mock_s.sync_database_url = None
    mock_s.openai_api_key = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
        patch("src.infrastructure.adapters.llm_router.logger") as log,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service()
    assert type(svc).__name__ == "LangGraphOllamaLlmAdapter"
    log.warning.assert_called_once()
    kwa = log.warning.call_args.kwargs
    assert kwa.get("llm_backend_solicitado") == "anthropic"
    assert kwa.get("evento") == "llm_plano_fallback_backend"
    assert kwa.get("tier") == "standard"


def test_perfil_empresa_questionario_rejeita_uf_invalida() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="XX",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="12345678000195",
        )
    assert ei.value.status_code == 400


def test_perfil_empresa_questionario_rejeita_cnpj_tamanho() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="123",
        )
    assert ei.value.status_code == 400


def test_singleton_ci_playwright_repo_reutiliza_instancia() -> None:
    deps.reset_ci_playwright_diagnostico_singleton()

    a = deps._singleton_ci_playwright_repo()
    b = deps._singleton_ci_playwright_repo()
    assert a is b

    deps.reset_ci_playwright_diagnostico_singleton()


def test_get_lead_vinculo_memoria_quando_ci_sem_dsn_via_settings_mock() -> None:
    """Pydantic rejeita ``QDI_CI_PLAYWRIGHT_INTEGRATED`` sem DATABASE_URL — mockamos ``get_settings``."""
    mock_s = MagicMock()
    mock_s.sync_database_url = None
    mock_s.ci_playwright_integrated = True
    mock_s.self_service_tenant_id = uuid4()

    deps.reset_ci_playwright_diagnostico_singleton()
    try:
        with patch("src.presentation.api.deps_repositories_core.get_settings", return_value=mock_s):
            port = deps.get_lead_diagnostico_vinculo_port()
        assert isinstance(port, MemoriaLeadDiagnosticoVinculoAdapter)
    finally:
        deps.reset_ci_playwright_diagnostico_singleton()


def test_get_lead_nop_sem_dsn_sem_ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("QDI_CI_PLAYWRIGHT_INTEGRATED", raising=False)
    get_settings.cache_clear()
    port = deps.get_lead_diagnostico_vinculo_port()
    assert isinstance(port, NopLeadDiagnosticoVinculoAdapter)


def test_get_normativa_score_macro_postgres_com_dsn() -> None:
    mock_s = MagicMock()
    mock_s.sync_database_url = "postgresql://user:pass@localhost/db"
    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s):
        repo = deps.get_normativa_score_macro_repository()
    assert isinstance(repo, PostgresNormativaScoreMacroRepository)


def test_get_normativa_score_macro_embutidas_sem_dsn() -> None:
    mock_s = MagicMock()
    mock_s.sync_database_url = None
    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s):
        repo = deps.get_normativa_score_macro_repository()
    assert isinstance(repo, EmbutidasNormativaScoreMacroRepository)


def test_perfil_empresa_questionario_rejeita_cnpj_nao_numerico() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="12.345.678/0001-95",
        )
    assert ei.value.status_code == 400
    assert "dígitos" in str(ei.value.detail)


def test_perfil_empresa_questionario_rejeita_cnpj_todos_iguais() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="1" * 14,
        )
    assert ei.value.status_code == 400


def test_perfil_empresa_questionario_rejeita_cnpj_dv_invalido() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="12345678000194",
        )
    assert ei.value.status_code == 400


def test_perfil_empresa_questionario_rejeita_cnae_nao_numerico() -> None:
    with pytest.raises(HTTPException) as ei:
        deps.perfil_empresa_para_questionario(
            razao_social="Empresa SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="123456A",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
            faixa_faturamento=None,
            cnpj="",
        )
    assert ei.value.status_code == 400
