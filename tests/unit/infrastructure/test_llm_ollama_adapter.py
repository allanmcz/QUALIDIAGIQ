"""Testes do adapter Ollama — timeout HTTP configurável (Settings)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter


@pytest.mark.asyncio
async def test_ollama_passa_timeout_para_httpx_async_client() -> None:
    """``OLLAMA_TIMEOUT_SECONDS`` materializa-se no construtor do ``httpx.AsyncClient``."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(
        return_value={"response": "Ação sugerida conforme LC 214/2025 art. 5º."}
    )

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", autospec=True) as mock_ac_cls:
        mock_ac_cls.return_value = mock_client_instance

        adapter = OllamaLlmAdapter(
            ollama_url="http://127.0.0.1:11434",
            model="llama3",
            timeout_seconds=12.5,
        )
        out = await adapter.gerar_recomendacao("Empresa X", "LC 214/2025")

        mock_ac_cls.assert_called_once()
        assert mock_ac_cls.call_args.kwargs.get("timeout") == 12.5
        assert "LC 214/2025" in out
