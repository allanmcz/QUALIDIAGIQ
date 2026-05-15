from __future__ import annotations

from abc import ABC, abstractmethod


class LlmServicePort(ABC):
    """
    Port (interface) para o serviço de Large Language Models.

    Responsabilidade: isolar a camada de aplicação de SDKs específicos (Ollama, Anthropic).

    Implementações: ``src/infrastructure/adapters/llm_*.py`` — selecção central em **ADR-021**
    (``build_llm_adapter_from_settings`` em ``llm_adapter_factory.py``). **ADR-022:** governação por tarefa
    via ``LlmGatewayRouter`` em ``src/infrastructure/llm/`` (fase incremental).
    """

    @abstractmethod
    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        """
        Recebe o contexto da empresa (respostas, pontuações) e a base normativa
        e devolve um parágrafo/texto em markdown com a recomendação da IA.
        """
