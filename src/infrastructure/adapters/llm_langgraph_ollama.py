"""
Adapter LLM: LangGraph orquestra um nó LangChain **ChatOllama** (servidor Ollama).

Camada: Infrastructure — implementa ``LlmServicePort``.

Decisão de produto: **ADR-007** — stack diferenciada (grafo extensível para RAG,
multi-passo, ferramentas) sem abdicar do Ollama em dev/self-hosted.
"""

from __future__ import annotations

from typing import Any, TypedDict

import structlog
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.lexiq_guardrail import filtrar_resposta_recomendacao_llm
from src.infrastructure.adapters.llm_recomendacao_prompt import montar_prompt_recomendacao

logger = structlog.get_logger(__name__)


class _EstadoRecomendacao(TypedDict):
    """Estado mínimo do grafo (um nó hoje; preparado para ramificações futuras)."""

    contexto_empresa: str
    base_normativa: str
    texto: str


class LangGraphOllamaLlmAdapter(LlmServicePort):
    """Recomendação via grafo LangGraph + modelo local Ollama (LangChain)."""

    def __init__(
        self,
        ollama_url: str = "http://127.0.0.1:11434",
        model: str = "llama3",
        *,
        timeout_seconds: float = 30.0,
        base_normativa_port: BaseNormativaPort | None = None,
        rag_similarity_threshold: float = 0.65,
    ) -> None:
        base = ollama_url.strip().rstrip("/")
        self._normativa_port = base_normativa_port
        self._rag_threshold = float(rag_similarity_threshold)
        self._llm = ChatOllama(
            base_url=base,
            model=model.strip(),
            temperature=0.2,
            async_client_kwargs={"timeout": timeout_seconds},
        )
        self._graph = self._compilar_grafo()

    def _compilar_grafo(self) -> Any:
        """Compila grafo single-node (entrada → recomendação → fim)."""

        async def no_recomendacao(state: _EstadoRecomendacao) -> _EstadoRecomendacao:
            prompt = montar_prompt_recomendacao(
                state["contexto_empresa"],
                state["base_normativa"],
            )
            msg = await self._llm.ainvoke([HumanMessage(content=prompt)])
            raw = getattr(msg, "content", None)
            texto = str(raw).strip() if raw is not None else ""
            return {**state, "texto": texto}

        g: StateGraph[_EstadoRecomendacao] = StateGraph(_EstadoRecomendacao)
        g.add_node("recomendacao", no_recomendacao)
        g.set_entry_point("recomendacao")
        g.add_edge("recomendacao", END)
        return g.compile()

    async def gerar_recomendacao(self, contexto_empresa: str, base_normativa: str) -> str:
        try:
            final = await self._graph.ainvoke(
                {
                    "contexto_empresa": contexto_empresa,
                    "base_normativa": base_normativa,
                    "texto": "",
                },
            )
            out = str(final.get("texto", "")).strip()
            return await filtrar_resposta_recomendacao_llm(
                out,
                base_normativa_port=self._normativa_port,
                rag_threshold=self._rag_threshold,
            )
        except Exception as exc:
            logger.warning(
                "langgraph_ollama_erro",
                erro=str(exc),
                exc_info=True,
            )
            return (
                "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
                "personalizada não pôde ser gerada no momento."
            )
