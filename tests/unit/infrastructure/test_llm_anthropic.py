"""Testes do adapter Anthropic (mock de rede)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.adapters.llm_anthropic import AnthropicLlmAdapter, _extrair_texto_resposta


def test_extrair_texto_resposta_ignora_blocos_nao_text() -> None:
    """Ramo em que o bloco não é ``type == \"text\"`` (blocos ferramenta / imagem)."""
    msg = SimpleNamespace(
        content=[
            SimpleNamespace(type="tool_use", name="noop"),
            SimpleNamespace(type="text", text="  só isto  "),
        ]
    )
    assert _extrair_texto_resposta(msg) == "só isto"


@pytest.mark.asyncio
async def test_anthropic_extrai_texto_e_passa_guardrail_regex() -> None:
    """Resposta com âncora LC 214/2025 deve ser preservada após o guardrail."""
    bloco = SimpleNamespace(type="text", text="Priorize LC 214/2025 no cronograma.")
    msg = SimpleNamespace(content=[bloco])
    mock_create = AsyncMock(return_value=msg)
    mock_client = MagicMock()
    mock_client.messages.create = mock_create

    with patch(
        "src.infrastructure.adapters.llm_anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        adapter = AnthropicLlmAdapter(api_key="sk-test", model="claude-haiku-4-5")
        out = await adapter.gerar_recomendacao("Empresa X", "Resumo")

    assert "LC 214/2025" in out
    mock_create.assert_awaited_once()


@pytest.mark.asyncio
async def test_anthropic_erro_rede_retorna_mensagem_estavel() -> None:
    """Falha na API não deve levantar exceção ao usuário final."""
    mock_create = AsyncMock(side_effect=RuntimeError("timeout"))
    mock_client = MagicMock()
    mock_client.messages.create = mock_create

    with patch(
        "src.infrastructure.adapters.llm_anthropic.AsyncAnthropic",
        return_value=mock_client,
    ):
        adapter = AnthropicLlmAdapter(api_key="sk-test", model="claude-haiku-4-5")
        out = await adapter.gerar_recomendacao("Empresa Y", "base")

    assert "indisponibilidade" in out.lower()
