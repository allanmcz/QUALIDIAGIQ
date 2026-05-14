"""Testes de ``llm_router`` — selecção de adapter sem I/O (ADR-021)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.llm_anthropic import AnthropicLlmAdapter
from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.adapters.llm_openai import OpenAiChatLlmAdapter
from src.infrastructure.adapters.llm_router import build_llm_adapter_from_settings


class TestBuildLlmAdapterFromSettings:
    """Garante precedência openai → anthropic → http_ollama → langgraph e log ``llm_router_resolvido``."""

    def test_http_ollama(self) -> None:
        mock_s = MagicMock()
        mock_s.qdi_llm_default_tier = "local"
        mock_s.llm_backend = "http_ollama"
        mock_s.anthropic_api_key = None
        mock_s.ollama_base_url = "http://localhost:11434"
        mock_s.ollama_model = "mistral"
        mock_s.ollama_timeout_seconds = 11.0
        mock_s.anthropic_model = "ignored"

        norm = MagicMock()
        with patch("src.infrastructure.adapters.llm_router.logger") as log:
            svc = build_llm_adapter_from_settings(
                mock_s,
                base_normativa_port=norm,
                rag_similarity_threshold=0.4,
            )
        assert isinstance(svc, OllamaLlmAdapter)
        log.info.assert_called_once()
        info_kw = log.info.call_args.kwargs
        assert info_kw.get("evento") == "llm_router_resolvido"
        assert info_kw.get("adapter") == "http_ollama"
        assert info_kw.get("tier") == "local"

    def test_openai_com_chave(self) -> None:
        mock_s = MagicMock()
        mock_s.qdi_llm_default_tier = "standard"
        mock_s.llm_backend = "openai"
        fk = MagicMock()
        fk.get_secret_value.return_value = "sk-openai-test"
        mock_s.openai_api_key = fk
        mock_s.openai_chat_model = "gpt-4o-mini"
        mock_s.anthropic_api_key = None
        mock_s.anthropic_model = "ignored"
        mock_s.ollama_base_url = "http://127.0.0.1:11434"
        mock_s.ollama_model = "llama3"
        mock_s.ollama_timeout_seconds = 30.0

        norm = MagicMock()
        with patch("src.infrastructure.adapters.llm_router.logger") as log:
            svc = build_llm_adapter_from_settings(
                mock_s,
                base_normativa_port=norm,
                rag_similarity_threshold=0.5,
            )
        assert isinstance(svc, OpenAiChatLlmAdapter)
        log.info.assert_called_once()
        kwa = log.info.call_args.kwargs
        assert kwa.get("adapter") == "openai_chat"
        assert kwa.get("tier") == "standard"
        assert kwa.get("modelo_openai") == "gpt-4o-mini"

    def test_openai_sem_chave_cai_langgraph(self) -> None:
        mock_s = MagicMock()
        mock_s.qdi_llm_default_tier = "local"
        mock_s.llm_backend = "openai"
        mock_s.openai_api_key = None
        mock_s.openai_chat_model = "gpt-4o-mini"
        mock_s.anthropic_api_key = None
        mock_s.anthropic_model = "claude-3-5-sonnet-20241022"
        mock_s.ollama_base_url = "http://host.docker.internal:11434"
        mock_s.ollama_model = "llama3"
        mock_s.ollama_timeout_seconds = 30.0

        norm = MagicMock()
        with patch("src.infrastructure.adapters.llm_router.logger") as log:
            svc = build_llm_adapter_from_settings(
                mock_s,
                base_normativa_port=norm,
                rag_similarity_threshold=0.6,
            )
        assert isinstance(svc, LangGraphOllamaLlmAdapter)
        log.warning.assert_called_once()
        wkw = log.warning.call_args.kwargs
        assert wkw.get("evento") == "llm_plano_fallback_backend"
        assert wkw.get("llm_backend_solicitado") == "openai"
        log.info.assert_called_once()
        assert log.info.call_args.kwargs.get("adapter") == "langgraph_ollama"

    def test_anthropic_com_chave(self) -> None:
        mock_s = MagicMock()
        mock_s.qdi_llm_default_tier = "premium"
        mock_s.llm_backend = "anthropic"
        fk = MagicMock()
        fk.get_secret_value.return_value = "sk-ant-test"
        mock_s.anthropic_api_key = fk
        mock_s.anthropic_model = "claude-3-haiku-latest"
        mock_s.ollama_base_url = "http://127.0.0.1:11434"
        mock_s.ollama_model = "llama3"
        mock_s.ollama_timeout_seconds = 30.0

        norm = MagicMock()
        with patch("src.infrastructure.adapters.llm_router.logger") as log:
            svc = build_llm_adapter_from_settings(
                mock_s,
                base_normativa_port=norm,
                rag_similarity_threshold=0.5,
            )
        assert isinstance(svc, AnthropicLlmAdapter)
        log.info.assert_called_once()
        assert log.info.call_args.kwargs.get("adapter") == "anthropic"
        assert log.info.call_args.kwargs.get("tier") == "premium"

    def test_default_langgraph(self) -> None:
        mock_s = MagicMock()
        mock_s.qdi_llm_default_tier = "local"
        mock_s.llm_backend = "langgraph_ollama"
        mock_s.anthropic_api_key = None
        mock_s.ollama_base_url = "http://host.docker.internal:11434"
        mock_s.ollama_model = "llama3"
        mock_s.ollama_timeout_seconds = 30.0
        mock_s.anthropic_model = "claude-3-5-sonnet-20241022"

        norm = MagicMock()
        with patch("src.infrastructure.adapters.llm_router.logger") as log:
            svc = build_llm_adapter_from_settings(
                mock_s,
                base_normativa_port=norm,
                rag_similarity_threshold=0.65,
            )
        assert isinstance(svc, LangGraphOllamaLlmAdapter)
        log.info.assert_called_once()
        kwa = log.info.call_args.kwargs
        assert kwa.get("adapter") == "langgraph_ollama"
        assert kwa.get("ollama_host") == "host.docker.internal"
