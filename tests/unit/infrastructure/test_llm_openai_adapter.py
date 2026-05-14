"""Testes do adapter OpenAI Chat — sem rede (mocks)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openai import APIError, RateLimitError

from src.infrastructure.adapters.llm_openai import OpenAiChatLlmAdapter


class TestOpenAiChatLlmAdapter:
    """Garante chamada à API, guardrail Lexiq e métricas sem I/O real."""

    @pytest.mark.asyncio
    async def test_gerar_recomendacao_sucesso_passa_pelo_guardrail(self) -> None:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content="  texto bruto  "))]
        mock_create = AsyncMock(return_value=mock_resp)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with (
            patch("src.infrastructure.adapters.llm_openai.AsyncOpenAI", return_value=mock_client),
            patch(
                "src.infrastructure.adapters.llm_openai.filtrar_resposta_recomendacao_llm",
                new_callable=AsyncMock,
            ) as filt,
        ):
            filt.return_value = "OK filtrado"
            ad = OpenAiChatLlmAdapter(api_key="sk-test", model="gpt-4o-mini")
            out = await ad.gerar_recomendacao("ctx", "norma")

        assert out == "OK filtrado"
        mock_create.assert_awaited_once()
        filt.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_gerar_recomendacao_rate_limit_devolve_mensagem_estavel(self) -> None:
        req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        resp = httpx.Response(429, request=req)
        exc = RateLimitError("too many", response=resp, body=None)
        mock_create = AsyncMock(side_effect=exc)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with (
            patch("src.infrastructure.adapters.llm_openai.AsyncOpenAI", return_value=mock_client),
            patch("src.infrastructure.adapters.llm_openai.logger") as log,
        ):
            ad = OpenAiChatLlmAdapter(api_key="sk-test", model="gpt-4o-mini")
            out = await ad.gerar_recomendacao("ctx", "norma")

        assert "indisponibilidade" in out.lower()
        log.warning.assert_called_once()
        assert log.warning.call_args.args[0] == "openai_llm_rate_limit"

    @pytest.mark.asyncio
    async def test_gerar_recomendacao_api_error_devolve_mensagem_estavel(self) -> None:
        req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
        exc = APIError("server error", request=req, body=None)
        mock_create = AsyncMock(side_effect=exc)
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with (
            patch("src.infrastructure.adapters.llm_openai.AsyncOpenAI", return_value=mock_client),
            patch("src.infrastructure.adapters.llm_openai.logger") as log,
        ):
            ad = OpenAiChatLlmAdapter(api_key="sk-test", model="gpt-4o-mini")
            out = await ad.gerar_recomendacao("ctx", "norma")

        assert "indisponibilidade" in out.lower()
        log.warning.assert_called_once()
        assert log.warning.call_args.args[0] == "openai_llm_api_error"

    @pytest.mark.asyncio
    async def test_gerar_recomendacao_excecao_generica_devolve_mensagem_estavel(self) -> None:
        mock_create = AsyncMock(side_effect=ValueError("inesperado"))
        mock_client = MagicMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = mock_create

        with (
            patch("src.infrastructure.adapters.llm_openai.AsyncOpenAI", return_value=mock_client),
            patch("src.infrastructure.adapters.llm_openai.logger") as log,
        ):
            ad = OpenAiChatLlmAdapter(api_key="sk-test", model="gpt-4o-mini")
            out = await ad.gerar_recomendacao("ctx", "norma")

        assert "indisponibilidade" in out.lower()
        log.warning.assert_called_once()
        assert log.warning.call_args.args[0] == "openai_llm_erro"
