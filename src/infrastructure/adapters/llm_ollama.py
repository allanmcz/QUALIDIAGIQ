import httpx
import structlog

from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import (
    mensagem_rejeicao_guardrail,
    texto_tem_ancora_normativa,
)

logger = structlog.get_logger(__name__)


class OllamaLlmAdapter(LlmServicePort):
    """
    Adapter para comunicar com uma instância local do Ollama via API REST.
    """

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
        *,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.ollama_url = ollama_url
        self.model = model
        self._timeout_seconds = timeout_seconds

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = f"""
Você é um Consultor Tributário Sênior especialista na Reforma Tributária Brasileira (EC 132/2023 e LC 214/2025).
Baseado exclusivamente no resumo do Decreto nº 12.955/2026 abaixo, faça uma recomendação de ação curta e objetiva para a empresa.

--- BASE NORMATIVA (Decreto 12.955/2026) ---
{base_normativa}

--- CONTEXTO DA EMPRESA ---
{contexto_empresa}

Recomendação (obrigatório citar no texto pelo menos uma referência explícita dentre:
LC 214/2025, EC 132/2023 ou ABNT NBR 17301:2026):
"""
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
                if not texto_tem_ancora_normativa(out):
                    logger.info(
                        "ollama_guardrail_lexiq",
                        motivo="resposta_sem_ancora_normativa_reconhecivel",
                    )
                    return mensagem_rejeicao_guardrail()
                return out
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
