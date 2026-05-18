"""Testes do serviço RAG para explicação do score (Onda IA 1.1)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.application.ports.base_normativa_port import ChunkNormativo
from src.application.services.explicacao_score_rag import (
    RAG_STATUS_COM_FONTE,
    RAG_STATUS_INSUFICIENTE,
    chunks_para_fontes_rag,
    determinar_rag_status,
    montar_query_rag_explicacao_score,
    rag_recuperacao_insuficiente,
    recuperar_contexto_explicacao_score,
)


class TestExplicacaoScoreRag:
    """Consulta semântica e classificação de status."""

    def test_montar_query_inclui_score_e_dimensao(self) -> None:
        q = montar_query_rag_explicacao_score(
            72.5,
            {"dimensao_mais_critica": "Fiscal", "empresa_regime": "simples_nacional"},
        )
        assert "72.5" in q
        assert "Fiscal" in q
        assert "QualiDiagIQ" in q

    def test_determinar_rag_status_com_fonte(self) -> None:
        chunks = [ChunkNormativo(texto="x", score=0.7, fonte="PRD")]
        assert determinar_rag_status(chunks, threshold=0.65) == RAG_STATUS_COM_FONTE

    def test_determinar_rag_status_insuficiente(self) -> None:
        chunks = [ChunkNormativo(texto="x", score=0.3, fonte="PRD")]
        assert determinar_rag_status(chunks, threshold=0.65) == RAG_STATUS_INSUFICIENTE

    def test_rag_recuperacao_insuficiente_true_para_status_fracos(self) -> None:
        assert rag_recuperacao_insuficiente(RAG_STATUS_INSUFICIENTE) is True
        assert rag_recuperacao_insuficiente("nao_recuperado") is True
        assert rag_recuperacao_insuficiente(RAG_STATUS_COM_FONTE) is False

    def test_chunks_para_fontes_rag_limita_trecho(self) -> None:
        longo = "a" * 400
        fontes = chunks_para_fontes_rag(
            [
                ChunkNormativo(
                    texto=longo,
                    score=0.8,
                    fonte="F1",
                    catalogo_id="FONTE-001",
                    artigo="docs/x.md",
                )
            ]
        )
        assert len(fontes) == 1
        assert fontes[0]["fonte"] == "FONTE-001"
        trecho = str(fontes[0]["trecho"])
        assert trecho.endswith("…")
        assert len(trecho) <= 281

    @pytest.mark.asyncio
    async def test_recuperar_contexto_delega_ao_port(self) -> None:
        port = AsyncMock()
        port.buscar_contexto = AsyncMock(
            return_value=[
                ChunkNormativo(
                    texto="trecho",
                    score=0.9,
                    fonte="FONTE-002",
                    catalogo_id="FONTE-002",
                    classe="A",
                    artigo="art.1",
                )
            ]
        )
        chunks, status, evs = await recuperar_contexto_explicacao_score(
            port,
            60.0,
            {},
            top_k=3,
            threshold=0.5,
        )
        assert len(chunks) == 1
        assert status == "com_fonte"
        assert len(evs) == 1
        port.buscar_contexto.assert_awaited_once()
