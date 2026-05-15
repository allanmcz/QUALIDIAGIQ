"""
Fábrica do adapter LLM por configuração (Settings).

Camada: Infrastructure — política documentada em **ADR-021** (cruzamento ADR-003, ADR-007).
**ADR-022:** este módulo substitui o nome legado ``llm_router.py`` para evitar colisão com o
``LlmGatewayRouter`` convergente em ``src/infrastructure/llm/`` (porta de governação por tarefa).

Analogia (Winthor): é o «parâmetro de filial + política de preço» que decide qual motor de cálculo chamar —
aqui o «motor» é Anthropic vs Ollama vs LangGraph vs OpenAI Chat, sem expor SDK na camada de aplicação.
"""

from __future__ import annotations

from urllib.parse import urlparse

import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.llm_tier_observabilidade import resolver_tier_efetivo_observabilidade
from src.infrastructure.adapters.llm_anthropic import AnthropicLlmAdapter
from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.adapters.llm_openai import OpenAiChatLlmAdapter
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


def _host_sem_credenciais(url: str) -> str:
    """Extrai hostname para logs — sem path/query (evita ruído; nunca logar API keys)."""
    host = urlparse(url.strip()).hostname
    return host or "(sem host)"


def _ollama_stack(
    settings: Settings,
    *,
    base_normativa_port: BaseNormativaPort,
    rag_similarity_threshold: float,
) -> LangGraphOllamaLlmAdapter:
    return LangGraphOllamaLlmAdapter(
        ollama_url=settings.ollama_base_url.strip(),
        model=settings.ollama_model.strip(),
        timeout_seconds=float(settings.ollama_timeout_seconds),
        base_normativa_port=base_normativa_port,
        rag_similarity_threshold=float(rag_similarity_threshold),
    )


def build_llm_adapter_from_settings(
    settings: Settings,
    *,
    base_normativa_port: BaseNormativaPort,
    rag_similarity_threshold: float,
    tier_use_case: str | None = None,
    tier_jwt_claim: str | None = None,
    perfil_conta_jwt: str | None = None,
) -> LlmServicePort:
    """
    Constrói o adapter LLM activo conforme ``QDI_LLM_BACKEND`` e segredos disponíveis.

    O tier efectivo para log segue **ADR-021 / plano 2.3.1** (``resolver_tier_efetivo_observabilidade``);
    a selecção do adapter continua governada por ``llm_backend`` + segredos.
    """
    thr = float(rag_similarity_threshold)
    url = settings.ollama_base_url.strip()
    model = settings.ollama_model.strip()
    timeout = float(settings.ollama_timeout_seconds)
    tier_efetivo, tier_fonte = resolver_tier_efetivo_observabilidade(
        tier_use_case=tier_use_case,
        tier_jwt_claim=tier_jwt_claim,
        perfil_conta_jwt=perfil_conta_jwt,
        settings_default_tier=str(settings.qdi_llm_default_tier),
        app_env=str(settings.app_env or "development"),
    )
    tier_settings_default = str(settings.qdi_llm_default_tier)

    resolved_label: str
    adapter: LlmServicePort

    if settings.llm_backend == "openai":
        okey = settings.openai_api_key.get_secret_value().strip() if settings.openai_api_key else ""
        ak = (
            settings.anthropic_api_key.get_secret_value().strip()
            if settings.anthropic_api_key
            else ""
        )
        if okey:
            resolved_label = "openai_chat"
            adapter = OpenAiChatLlmAdapter(
                api_key=okey,
                model=settings.openai_chat_model.strip(),
                base_normativa_port=base_normativa_port,
                rag_similarity_threshold=thr,
            )
        elif settings.qdi_llm_openai_fallback_anthropic and ak:
            logger.info(
                "llm_openai_indisponivel_fallback_anthropic",
                evento="llm_plano_fallback_backend",
                tier=tier_efetivo,
                tier_fonte=tier_fonte,
                tier_settings_default=tier_settings_default,
                llm_backend_solicitado="openai",
                fallback="anthropic",
            )
            resolved_label = "anthropic"
            adapter = AnthropicLlmAdapter(
                api_key=ak,
                model=settings.anthropic_model.strip(),
                base_normativa_port=base_normativa_port,
                rag_similarity_threshold=thr,
            )
        else:
            logger.warning(
                "llm_backend_openai_sem_api_key",
                fallback="langgraph_ollama",
                llm_backend_solicitado="openai",
                evento="llm_plano_fallback_backend",
                tier=tier_efetivo,
                tier_fonte=tier_fonte,
                tier_settings_default=tier_settings_default,
            )
            resolved_label = "langgraph_ollama"
            adapter = _ollama_stack(
                settings, base_normativa_port=base_normativa_port, rag_similarity_threshold=thr
            )
    elif settings.llm_backend == "anthropic":
        ak = (
            settings.anthropic_api_key.get_secret_value().strip()
            if settings.anthropic_api_key
            else ""
        )
        if ak:
            resolved_label = "anthropic"
            adapter = AnthropicLlmAdapter(
                api_key=ak,
                model=settings.anthropic_model.strip(),
                base_normativa_port=base_normativa_port,
                rag_similarity_threshold=thr,
            )
        else:
            logger.warning(
                "llm_backend_anthropic_sem_api_key",
                fallback="langgraph_ollama",
                llm_backend_solicitado="anthropic",
                evento="llm_plano_fallback_backend",
                tier=tier_efetivo,
                tier_fonte=tier_fonte,
                tier_settings_default=tier_settings_default,
            )
            resolved_label = "langgraph_ollama"
            adapter = _ollama_stack(
                settings, base_normativa_port=base_normativa_port, rag_similarity_threshold=thr
            )
    elif settings.llm_backend == "http_ollama":
        resolved_label = "http_ollama"
        adapter = OllamaLlmAdapter(
            ollama_url=url,
            model=model,
            timeout_seconds=timeout,
            base_normativa_port=base_normativa_port,
            rag_similarity_threshold=thr,
        )
    else:
        resolved_label = "langgraph_ollama"
        adapter = _ollama_stack(
            settings, base_normativa_port=base_normativa_port, rag_similarity_threshold=thr
        )

    logger.info(
        "llm_router_resolvido",
        evento="llm_router_resolvido",
        tier=tier_efetivo,
        tier_fonte=tier_fonte,
        tier_settings_default=tier_settings_default,
        llm_backend=settings.llm_backend,
        adapter=resolved_label,
        modelo_ollama=model if resolved_label not in ("anthropic", "openai_chat") else None,
        modelo_claude=settings.anthropic_model.strip() if resolved_label == "anthropic" else None,
        modelo_openai=(
            settings.openai_chat_model.strip() if resolved_label == "openai_chat" else None
        ),
        openai_politica_fallback_anthropic=(
            settings.llm_backend == "openai" and resolved_label == "anthropic"
        ),
        ollama_host=_host_sem_credenciais(url),
    )
    return adapter
