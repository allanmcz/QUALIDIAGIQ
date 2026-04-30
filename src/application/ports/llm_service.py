from typing import Protocol

class LlmServicePort(Protocol):
    """
    Port (Interface) para o serviço de Large Language Models.
    Responsabilidade: Isolar a camada de aplicação de SDKs específicos (Ollama, OpenAI, Anthropic).
    """

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        """
        Recebe o contexto da empresa (respostas, pontuações) e a base normativa
        e devolve um parágrafo/texto em markdown com a recomendação da IA.
        """
        ...
