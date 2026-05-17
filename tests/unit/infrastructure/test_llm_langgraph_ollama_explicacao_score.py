"""Guardrail modo explicação-score no adapter LangGraph Ollama."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from src.application.services.lexiq_guardrail import _RODAPE_ANCORAS_EXPLICACAO_SCORE
from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_prompt_modo import PROMPT_MODO_TEXTO_LIVRE


@pytest.mark.asyncio
async def test_modo_texto_livre_preserva_parecer_sem_ancora_literal() -> None:
    """Explicação do score: parecer longo sem LC/EC/ABNT no corpo recebe rodapé, não rejeição."""
    parecer_llm = (
        "Na minha leitura, o score indica maturidade intermediária na transição tributária. "
        "A empresa deve priorizar adequação de cadastros e alinhamento do ERP aos novos fluxos "
        "de documentos fiscais antes do cronograma de 2026, com foco na dimensão fiscal."
    )
    with patch(
        "src.infrastructure.adapters.llm_langgraph_ollama.ChatOllama",
    ) as mock_cls:
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content=parecer_llm))
        mock_cls.return_value = mock_llm

        adapter = LangGraphOllamaLlmAdapter(
            ollama_url="http://127.0.0.1:11434",
            model="llama3",
        )
        out = await adapter.gerar_recomendacao("prompt explicacao score", PROMPT_MODO_TEXTO_LIVRE)

    assert parecer_llm in out
    assert _RODAPE_ANCORAS_EXPLICACAO_SCORE in out
    assert not out.startswith("Recomendação não exibida:")
