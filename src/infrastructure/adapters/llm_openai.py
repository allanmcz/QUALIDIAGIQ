"""
Adapter OpenAI Chat Completions — implementa ``LlmServicePort``.

Camada: Infrastructure
Requer ``OPENAI_API_KEY``; modelo configurável (``OPENAI_CHAT_MODEL`` / ``QDI_OPENAI_CHAT_MODEL``).

Base normativa (previsibilidade ao contribuinte): LC 214/2025 — saídas de IA passam pelo guardrail Lexiq.
"""

from __future__ import annotations

import structlog
from openai import APIError, AsyncOpenAI, RateLimitError

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import aplicar_guardrail_saida_llm
from src.infrastructure.adapters.llm_prompt_modo import PROMPT_MODO_TEXTO_LIVRE
from src.infrastructure.adapters.llm_recomendacao_prompt import montar_prompt_recomendacao
from src.infrastructure.observability.qdi_otel_metrics import record_llm_recommendation

logger = structlog.get_logger(__name__)

_MENSAGEM_INDISPONIVEL = (
    "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
    "personalizada não pôde ser gerada no momento."
)


class OpenAiChatLlmAdapter(LlmServicePort):
    """Recomendações via API Chat Completions (OpenAI)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        base_normativa_port: BaseNormativaPort | None = None,
        rag_similarity_threshold: float = 0.65,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key.strip())
        self._model = model.strip()
        self._max_tokens = int(max_tokens)
        self._temperature = float(temperature)
        self._normativa_port = base_normativa_port
        self._rag_threshold = float(rag_similarity_threshold)

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = (
            contexto_empresa.strip()
            if base_normativa == PROMPT_MODO_TEXTO_LIVRE
            else montar_prompt_recomendacao(contexto_empresa, base_normativa)
        )
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            choice0 = resp.choices[0] if resp.choices else None
            raw = getattr(choice0, "message", None)
            content = getattr(raw, "content", None) if raw is not None else None
            out = str(content).strip() if content is not None else ""
            result = await aplicar_guardrail_saida_llm(
                out,
                modo_explicacao_score=base_normativa == PROMPT_MODO_TEXTO_LIVRE,
                base_normativa_port=self._normativa_port,
                rag_threshold=self._rag_threshold,
            )
            record_llm_recommendation(adapter="openai_chat", outcome="success")
            return result
        except RateLimitError as exc:
            record_llm_recommendation(adapter="openai_chat", outcome="http_error")
            logger.warning(
                "openai_llm_rate_limit",
                erro=str(exc),
                modelo=self._model,
            )
            if base_normativa == PROMPT_MODO_TEXTO_LIVRE:
                raise
            return _MENSAGEM_INDISPONIVEL
        except APIError as exc:
            record_llm_recommendation(adapter="openai_chat", outcome="http_error")
            logger.warning(
                "openai_llm_api_error",
                erro=str(exc),
                modelo=self._model,
            )
            if base_normativa == PROMPT_MODO_TEXTO_LIVRE:
                raise
            return _MENSAGEM_INDISPONIVEL
        except Exception as exc:
            record_llm_recommendation(adapter="openai_chat", outcome="unexpected_error")
            logger.warning(
                "openai_llm_erro",
                erro=str(exc),
                modelo=self._model,
                exc_info=True,
            )
            if base_normativa == PROMPT_MODO_TEXTO_LIVRE:
                raise
            return _MENSAGEM_INDISPONIVEL
