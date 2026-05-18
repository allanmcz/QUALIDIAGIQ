"""Ramos extras de factories em ``dependencies.py`` (LLM, base normativa, query perfil empresa)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request

from src.application.ports.lead_diagnostico_vinculo_port import (
    NopLeadDiagnosticoVinculoAdapter,
)
from src.application.use_cases.explicar_score_llm_use_case import ExplicarScoreLlmUseCase
from src.domain.entities.diagnostico import PorteEmpresa, RegimeTributario, SetorMacro
from src.infrastructure.config.settings import get_settings
from src.infrastructure.diagnosticos.memoria_lead_diagnostico_vinculo import (
    MemoriaLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.llm.gateway_router import LlmGatewayRouter
from src.infrastructure.repositories.embutidas_normativa_pergunta_peso_repository import (
    EmbutidasNormativaPerguntaPesoRepository,
)
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository import (
    PostgresNormativaPerguntaPesoRepository,
)
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api import dependencies as deps
from src.presentation.api import deps_auth_supabase


def _http_request_vazio() -> Request:
    """Request ASGI mínimo para ``Depends(get_llm_service)`` em testes unitários."""
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("test", 80),
    }
    return Request(scope)


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
    m.qdi_rag_backend = "pgvector"
    m.ollama_base_url = "http://127.0.0.1:11434"
    m.ollama_embedding_model = "mxbai-embed-large:latest"
    m.qdi_rag_incluir_adrs = True
    m.qdi_rag_codigo_index_path = ".cache/test.json"
    m.ollama_timeout_seconds = 30.0

    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=m):
        port = deps.build_base_normativa_port()
    assert type(port).__name__ == "PgvectorBaseNormativaAdapter"


def test_build_base_normativa_auto_compoe_pgvector_e_ollama(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://x:y@127.0.0.1:1/db")

    fk = MagicMock()
    fk.get_secret_value.return_value = "sk-test-openai-xxxx"

    m = MagicMock()
    m.sync_database_url = "postgresql://x:y@127.0.0.1:1/db"
    m.openai_api_key = fk
    m.openai_embedding_model = "text-embedding-3-small"
    m.qdi_rag_backend = "auto"
    m.ollama_base_url = "http://127.0.0.1:11434"
    m.ollama_embedding_model = "mxbai-embed-large:latest"
    m.qdi_rag_incluir_adrs = False
    m.qdi_rag_codigo_index_path = ""
    m.ollama_timeout_seconds = 30.0

    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=m):
        port = deps.build_base_normativa_port()
    assert type(port).__name__ == "CompositeBaseNormativaAdapter"


def test_get_llm_http_ollama_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = False
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
        svc = deps.get_llm_service(_http_request_vazio())
    assert type(svc).__name__ == "OllamaLlmAdapter"


def test_get_llm_anthropic_com_chave_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = False
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
        svc = deps.get_llm_service(_http_request_vazio())
    assert type(svc).__name__ == "AnthropicLlmAdapter"


def test_get_llm_openai_com_chave_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = False
    mock_s.qdi_llm_default_tier = "standard"
    mock_s.llm_backend = "openai"
    fk_o = MagicMock()
    fk_o.get_secret_value.return_value = "sk-openai-test"
    mock_s.openai_api_key = fk_o
    mock_s.openai_chat_model = "gpt-4o-mini"
    mock_s.anthropic_api_key = None
    mock_s.anthropic_model = "ignored"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "fallback"
    mock_s.ollama_timeout_seconds = 20.0
    mock_s.qdi_rag_similarity_threshold = "0.21"
    mock_s.sync_database_url = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service(_http_request_vazio())
    assert type(svc).__name__ == "OpenAiChatLlmAdapter"


def test_get_llm_openai_sem_chave_fallback_langgraph() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = False
    mock_s.qdi_llm_default_tier = "local"
    mock_s.llm_backend = "openai"
    mock_s.openai_api_key = None
    mock_s.openai_chat_model = "gpt-4o-mini"
    fk = MagicMock()
    fk.get_secret_value.return_value = ""
    mock_s.anthropic_api_key = fk
    mock_s.anthropic_model = "x"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "m"
    mock_s.ollama_timeout_seconds = 9.0
    mock_s.qdi_rag_similarity_threshold = "0.13"
    mock_s.sync_database_url = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
        patch("src.infrastructure.adapters.llm_adapter_factory.logger") as log,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service(_http_request_vazio())
    assert type(svc).__name__ == "LangGraphOllamaLlmAdapter"
    log.warning.assert_called_once()
    kwa = log.warning.call_args.kwargs
    assert kwa.get("llm_backend_solicitado") == "openai"
    assert kwa.get("evento") == "llm_plano_fallback_backend"


def test_get_llm_openai_sem_chave_politica_anthropic_adapter() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = True
    mock_s.qdi_llm_default_tier = "premium"
    mock_s.llm_backend = "openai"
    mock_s.openai_api_key = None
    mock_s.openai_chat_model = "gpt-4o-mini"
    fk_a = MagicMock()
    fk_a.get_secret_value.return_value = "sk-ant-fallback"
    mock_s.anthropic_api_key = fk_a
    mock_s.anthropic_model = "claude-3-haiku-latest"
    mock_s.ollama_base_url = "http://localhost:11434"
    mock_s.ollama_model = "m"
    mock_s.ollama_timeout_seconds = 9.0
    mock_s.qdi_rag_similarity_threshold = "0.13"
    mock_s.sync_database_url = None

    with (
        patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s),
        patch("src.presentation.api.deps_infra_services.build_base_normativa_port") as mock_bn,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service(_http_request_vazio())
    assert type(svc).__name__ == "AnthropicLlmAdapter"


def test_get_llm_anthropic_sem_chave_fallback_langgraph() -> None:
    mock_s = MagicMock()
    mock_s.qdi_llm_openai_fallback_anthropic = False
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
        patch("src.infrastructure.adapters.llm_adapter_factory.logger") as log,
    ):
        mock_bn.return_value = MagicMock()
        svc = deps.get_llm_service(_http_request_vazio())
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


def test_get_normativa_pergunta_peso_postgres_com_dsn() -> None:
    mock_s = MagicMock()
    mock_s.sync_database_url = "postgresql://user:pass@localhost/db"
    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s):
        repo = deps.get_normativa_pergunta_peso_repository()
    assert isinstance(repo, PostgresNormativaPerguntaPesoRepository)


def test_get_normativa_pergunta_peso_embutidas_sem_dsn() -> None:
    mock_s = MagicMock()
    mock_s.sync_database_url = None
    with patch("src.presentation.api.deps_infra_services.get_settings", return_value=mock_s):
        repo = deps.get_normativa_pergunta_peso_repository()
    assert isinstance(repo, EmbutidasNormativaPerguntaPesoRepository)


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


def test_get_llm_gateway_constroi_router() -> None:
    with patch("src.presentation.api.deps_infra_services.get_llm_service") as gs:
        gs.return_value = MagicMock()
        gw = deps.get_llm_gateway(_http_request_vazio())
    assert isinstance(gw, LlmGatewayRouter)


def test_get_llm_gateway_operacional_constroi_router() -> None:
    with patch("src.presentation.api.deps_infra_services.get_llm_service") as gs:
        gs.return_value = MagicMock()
        gw = deps.get_llm_gateway_operacional(_http_request_vazio())
    assert isinstance(gw, LlmGatewayRouter)


def test_get_explicar_score_llm_use_case_instancia() -> None:
    fake_gw = MagicMock()
    uc = deps.get_explicar_score_llm_use_case(fake_gw)
    assert isinstance(uc, ExplicarScoreLlmUseCase)


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
