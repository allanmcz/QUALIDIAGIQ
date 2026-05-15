"""Testes do adapter LangGraph + ChatOllama (mock de rede)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_prompt_modo import PROMPT_MODO_TEXTO_LIVRE


@pytest.mark.asyncio
async def test_langgraph_ollama_propaga_resposta_com_ancora_normativa() -> None:
    """Com ``ainvoke`` do modelo a devolver citação reconhecida, o texto passa o guardrail."""
    with patch(
        "src.infrastructure.adapters.llm_langgraph_ollama.ChatOllama",
    ) as mock_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="Ajuste crédito conforme LC 214/2025 art. 5º no plano de transição.",
            ),
        )
        mock_cls.return_value = mock_llm

        adapter = LangGraphOllamaLlmAdapter(
            ollama_url="http://127.0.0.1:11434",
            model="llama3",
            timeout_seconds=10.0,
        )
        out = await adapter.gerar_recomendacao("Empresa X", "Resumo normativo")

        assert "LC 214/2025" in out
        mock_llm.ainvoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_langgraph_ollama_guardrail_quando_sem_ancora() -> None:
    """Sem âncora Lexiq, devolve mensagem de rejeição estável."""
    with patch(
        "src.infrastructure.adapters.llm_langgraph_ollama.ChatOllama",
    ) as mock_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="Melhore processos internos e treine a equipe."),
        )
        mock_cls.return_value = mock_llm

        adapter = LangGraphOllamaLlmAdapter(
            ollama_url="http://127.0.0.1:11434",
            model="llama3",
        )
        out = await adapter.gerar_recomendacao("Empresa Y", "base")

        assert "Recomendação não exibida" in out


@pytest.mark.asyncio
async def test_langgraph_ollama_modo_texto_livre_usa_contexto_sem_template() -> None:
    """``PROMPT_MODO_TEXTO_LIVRE`` — prompt já montado (explicação score ADR-022)."""
    with patch(
        "src.infrastructure.adapters.llm_langgraph_ollama.ChatOllama",
    ) as mock_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(
                content="A dimensão fiscal exige atenção conforme LC 214/2025.",
            ),
        )
        mock_cls.return_value = mock_llm

        adapter = LangGraphOllamaLlmAdapter(
            ollama_url="http://127.0.0.1:11434",
            model="llama3",
        )
        prompt_completo = "Explique o score 52 sem recalcular (LC 214/2025)."
        out = await adapter.gerar_recomendacao(prompt_completo, PROMPT_MODO_TEXTO_LIVRE)

        assert "LC 214/2025" in out
        sent = mock_llm.ainvoke.call_args[0][0][0].content
        assert sent == prompt_completo
