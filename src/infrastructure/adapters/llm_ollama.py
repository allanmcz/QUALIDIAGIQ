import logging

import httpx

from src.application.ports.llm_service import LlmServicePort

logger = logging.getLogger(__name__)


class OllamaLlmAdapter(LlmServicePort):
    """
    Adapter para comunicar com uma instância local do Ollama via API REST.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "llama3"):
        self.ollama_url = ollama_url
        self.model = model

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        prompt = f"""
Você é um Consultor Tributário Sênior especialista na Reforma Tributária Brasileira (EC 132/2023 e LC 214/2025).
Baseado exclusivamente no resumo do Decreto nº 12.955/2026 abaixo, faça uma recomendação de ação curta e objetiva para a empresa.

--- BASE NORMATIVA (Decreto 12.955/2026) ---
{base_normativa}

--- CONTEXTO DA EMPRESA ---
{contexto_empresa}

Recomendação:
"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                return str(texto)
        except httpx.RequestError as exc:
            logger.warning(f"Erro de comunicação com o Ollama local: {exc}")
            return "Devido a indisponibilidade temporária do serviço de IA, a recomendação personalizada não pôde ser gerada no momento."
        except Exception as exc:
            logger.error(f"Erro inesperado no OllamaAdapter: {exc}")
            return "Erro ao processar a recomendação de IA."
