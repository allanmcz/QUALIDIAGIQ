from __future__ import annotations

from typing import cast

import httpx
import structlog
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import filtrar_resposta_recomendacao_llm
from src.infrastructure.adapters.llm_recomendacao_prompt import montar_prompt_recomendacao
from src.infrastructure.observability.qdi_otel_metrics import record_llm_recommendation

logger = structlog.get_logger(__name__)


def _transiente_httpx(exc: BaseException) -> bool:
    """Erros rede/5xx merecem nova tentativa (S-03 — resiliência ao Ollama)."""
    if isinstance(exc, httpx.RequestError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return False


class OllamaLlmAdapter(LlmServicePort):
    """
    Adapter legado: Ollama via API REST direta (httpx).

    Preferir ``LangGraphOllamaLlmAdapter`` (default) — ver ADR-007.
    """

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
        *,
        timeout_seconds: float = 30.0,
        base_normativa_port: BaseNormativaPort | None = None,
        rag_similarity_threshold: float = 0.65,
    ) -> None:
        self.ollama_url = ollama_url
        self.model = model
        self._timeout_seconds = timeout_seconds
        self._normativa_port = base_normativa_port
        self._rag_threshold = float(rag_similarity_threshold)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
        retry=retry_if_exception(_transiente_httpx),
        reraise=True,
    )
    async def _post_generate_json(
        self, client: httpx.AsyncClient, prompt: str
    ) -> dict[str, object]:
        response = await client.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
        )
        response.raise_for_status()
        return cast("dict[str, object]", response.json())

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = montar_prompt_recomendacao(contexto_empresa, base_normativa)
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                data = await self._post_generate_json(client, prompt)
                texto = data.get("response", "Recomendação não gerada pelo modelo.")
                out = str(texto).strip()
                result = await filtrar_resposta_recomendacao_llm(
                    out,
                    base_normativa_port=self._normativa_port,
                    rag_threshold=self._rag_threshold,
                )
                record_llm_recommendation(adapter="ollama_rest", outcome="success")
                return result
        except httpx.HTTPError as exc:
            record_llm_recommendation(adapter="ollama_rest", outcome="http_error")
            logger.warning(
                "ollama_http_error",
                erro=str(exc),
                url_host=self.ollama_url,
                model=self.model,
            )
            return "Devido a indisponibilidade temporária do serviço de IA, a recomendação personalizada não pôde ser gerada no momento."
        except Exception as exc:
            record_llm_recommendation(adapter="ollama_rest", outcome="unexpected_error")
            logger.error(
                "ollama_erro_inesperado",
                erro=str(exc),
                model=self.model,
                exc_info=True,
            )
            return "Erro ao processar a recomendação de IA."
