"""
Adapter Anthropic Messages API — implementa ``LlmServicePort`` (Sprint 12).

Camada: Infrastructure
Requer ``ANTHROPIC_API_KEY``; modelo configurável (default compatível com API atual).
"""

from __future__ import annotations

import structlog
from anthropic import AsyncAnthropic

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import filtrar_resposta_recomendacao_llm
from src.infrastructure.adapters.llm_recomendacao_prompt import montar_prompt_recomendacao
from src.infrastructure.observability.qdi_otel_metrics import record_llm_recommendation

logger = structlog.get_logger(__name__)


def _extrair_texto_resposta(msg: object) -> str:
    """Concatena blocos ``text`` da resposta Anthropic."""
    blocos = getattr(msg, "content", None) or []
    partes: list[str] = []
    for block in blocos:
        btipo = getattr(block, "type", None)
        if btipo == "text":
            partes.append(str(getattr(block, "text", "")))
    return "".join(partes).strip()


class AnthropicLlmAdapter(LlmServicePort):
    """Recomendações via Claude (async)."""

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
        self._client = AsyncAnthropic(api_key=api_key.strip())
        self._model = model.strip()
        self._max_tokens = max_tokens
        self._temperature = float(temperature)
        self._normativa_port = base_normativa_port
        self._rag_threshold = float(rag_similarity_threshold)

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = montar_prompt_recomendacao(contexto_empresa, base_normativa)
        try:
            msg = await self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            out = _extrair_texto_resposta(msg)
            result = await filtrar_resposta_recomendacao_llm(
                out,
                base_normativa_port=self._normativa_port,
                rag_threshold=self._rag_threshold,
            )
            record_llm_recommendation(adapter="anthropic", outcome="success")
            return result
        except Exception as exc:
            record_llm_recommendation(adapter="anthropic", outcome="unexpected_error")
            logger.warning(
                "anthropic_llm_erro",
                erro=str(exc),
                modelo=self._model,
                exc_info=True,
            )
            return (
                "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
                "personalizada não pôde ser gerada no momento."
            )
