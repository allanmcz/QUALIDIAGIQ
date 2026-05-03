import httpx
import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import filtrar_resposta_recomendacao_llm
from src.infrastructure.adapters.llm_recomendacao_prompt import montar_prompt_recomendacao

logger = structlog.get_logger(__name__)


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

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = montar_prompt_recomendacao(contexto_empresa, base_normativa)
        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
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
                data: dict[str, object] = response.json()
                texto = data.get("response", "Recomendação não gerada pelo modelo.")
                out = str(texto).strip()
                return await filtrar_resposta_recomendacao_llm(
                    out,
                    base_normativa_port=self._normativa_port,
                    rag_threshold=self._rag_threshold,
                )
        except httpx.RequestError as exc:
            logger.warning(
                "ollama_request_error",
                erro=str(exc),
                url_host=self.ollama_url,
            )
            return "Devido a indisponibilidade temporária do serviço de IA, a recomendação personalizada não pôde ser gerada no momento."
        except Exception as exc:
            logger.error(
                "ollama_erro_inesperado",
                erro=str(exc),
                exc_info=True,
            )
            return "Erro ao processar a recomendação de IA."
