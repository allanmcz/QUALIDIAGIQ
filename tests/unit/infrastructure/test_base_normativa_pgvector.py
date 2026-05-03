"""Testes unitários do adapter pgvector — mocks httpx + asyncpg (sem rede)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.adapters.base_normativa_pgvector import (
    PgvectorBaseNormativaAdapter,
    _embedding_openai,
    _vetor_para_sql_literal,
)


class TestVetorSqlLiteral:
    """Literal SQL para casting ``::vector``."""

    def test_formato_lista(self) -> None:
        s = _vetor_para_sql_literal([0.0, 0.5, 1.0])
        assert s.startswith("[") and s.endswith("]")
        assert "0.0" in s and "0.5" in s


@pytest.mark.asyncio
async def test_embedding_openai_extrai_vetor() -> None:
    """Resposta OpenAI mínima → lista de floats."""
    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json = MagicMock(
        return_value={"data": [{"embedding": [0.1, 0.2, 0.3]}]},
    )
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=fake_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        vec = await _embedding_openai("texto", api_key="sk-x", model="text-embedding-3-small")

    assert vec == [0.1, 0.2, 0.3]
    mock_client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_embedding_openai_texto_vazio_lanca() -> None:
    with pytest.raises(ValueError, match="vazio"):
        await _embedding_openai("  ", api_key="k", model="m")


@pytest.mark.asyncio
async def test_pgvector_adapter_buscar_contexto_com_mocks() -> None:
    """Fluxo: embedding OK + uma linha Postgres → ``ChunkNormativo``."""
    rows = [
        {
            "texto": "Trecho LC 214",
            "score": 0.88,
            "fonte": "LC 214/2025",
            "artigo": "art. 5º",
        },
    ]
    fake_conn = MagicMock()
    fake_conn.fetch = AsyncMock(return_value=rows)
    fake_conn.close = AsyncMock()

    with (
        patch(
            "src.infrastructure.adapters.base_normativa_pgvector._embedding_openai",
            new_callable=AsyncMock,
            return_value=[0.0] * 8,
        ),
        patch(
            "src.infrastructure.adapters.base_normativa_pgvector.asyncpg.connect",
            new_callable=AsyncMock,
            return_value=fake_conn,
        ),
    ):
        ad = PgvectorBaseNormativaAdapter(
            dsn="postgresql://u:p@localhost:5432/db",
            openai_api_key="sk",
        )
        out = await ad.buscar_contexto("consulta", top_k=3, threshold=0.5)

    assert len(out) == 1
    assert out[0].fonte == "LC 214/2025"
    assert out[0].score == 0.88
    fake_conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_pgvector_adapter_query_vazia_retorna_lista_vazia() -> None:
    ad = PgvectorBaseNormativaAdapter(
        dsn="postgresql://u:p@localhost:5432/db",
        openai_api_key="sk",
    )
    out = await ad.buscar_contexto("   ", top_k=3)
    assert out == []
