"""
Roteamento do adapter LLM por configuração (Settings).

Camada: Infrastructure — implementa política documentada em **ADR-021** (cruzamento ADR-003, ADR-007).

Analogia (Winthor): é o «parâmetro de filial + política de preço» que decide qual motor de cálculo chamar —
aqui o «motor» é Anthropic vs Ollama vs LangGraph, sem expor SDK na camada de aplicação.
"""

from __future__ import annotations

from urllib.parse import urlparse

import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.infrastructure.adapters.llm_anthropic import AnthropicLlmAdapter
from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


def _host_sem_credenciais(url: str) -> str:
    """Extrai hostname para logs — sem path/query (evita ruído; nunca logar API keys)."""
    host = urlparse(url.strip()).hostname
    return host or "(sem host)"


def build_llm_adapter_from_settings(
    settings: Settings,
    *,
    base_normativa_port: BaseNormativaPort,
    rag_similarity_threshold: float,
) -> LlmServicePort:
    """
    Constrói o adapter LLM activo conforme ``QDI_LLM_BACKEND`` e segredos disponíveis.

    O tier ``QDI_LLM_DEFAULT_TIER`` é registado em log para observabilidade; a selecção
    efectiva continua governada por ``llm_backend`` até política tenant/plano (roadmap).
    """
    thr = float(rag_similarity_threshold)
    url = settings.ollama_base_url.strip()
    model = settings.ollama_model.strip()
    timeout = float(settings.ollama_timeout_seconds)
    tier = settings.qdi_llm_default_tier

    resolved_label: str
    adapter: LlmServicePort

    if settings.llm_backend == "anthropic":
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
                tier=tier,
            )
            resolved_label = "langgraph_ollama"
            adapter = LangGraphOllamaLlmAdapter(
                ollama_url=url,
                model=model,
                timeout_seconds=timeout,
                base_normativa_port=base_normativa_port,
                rag_similarity_threshold=thr,
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
        adapter = LangGraphOllamaLlmAdapter(
            ollama_url=url,
            model=model,
            timeout_seconds=timeout,
            base_normativa_port=base_normativa_port,
            rag_similarity_threshold=thr,
        )

    logger.info(
        "llm_router_resolvido",
        evento="llm_router_resolvido",
        tier=tier,
        llm_backend=settings.llm_backend,
        adapter=resolved_label,
        modelo_ollama=model if resolved_label != "anthropic" else None,
        modelo_claude=settings.anthropic_model.strip() if resolved_label == "anthropic" else None,
        ollama_host=_host_sem_credenciais(url),
    )
    return adapter
