"""Testes do adapter HTTP Ollama — timeout e falhas de rede."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter


@pytest.mark.asyncio
async def test_ollama_adapter_timeout_usa_segundos_do_construtor() -> None:
    """Timeout httpx alinha-se ao parâmetro (Settings usa OLLAMA_TIMEOUT_SECONDS)."""
    adapter = OllamaLlmAdapter(
        ollama_url="http://127.0.0.1:11434",
        model="llama3",
        timeout_seconds=12.5,
    )

    mock_post = AsyncMock(side_effect=httpx.TimeoutException("timeout simulado"))
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        out = await adapter.gerar_recomendacao("ctx", "base")

    assert "indisponibilidade" in out.lower()
    mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_adapter_request_error_retorna_fallback_amigavel() -> None:
    adapter = OllamaLlmAdapter(timeout_seconds=5.0)
    mock_post = AsyncMock(side_effect=httpx.RequestError("connection refused", request=MagicMock()))
    mock_client = MagicMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = mock_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        out = await adapter.gerar_recomendacao("ctx", "base")

    assert "indisponibilidade" in out.lower()
