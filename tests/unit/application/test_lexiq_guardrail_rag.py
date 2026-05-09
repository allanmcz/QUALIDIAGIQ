"""Testes do guardrail Lexiq com RAG opcional (``BaseNormativaPort``)."""

from __future__ import annotations

import pytest

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo
from src.application.services.lexiq_guardrail import (
    filtrar_resposta_recomendacao_llm,
    mensagem_rejeicao_guardrail,
    validar_ancora_normativa_rag,
)


class _PortFake(BaseNormativaPort):
    """Port em memória para unit tests."""

    def __init__(self, chunks: list[ChunkNormativo]) -> None:
        self._chunks = list(chunks)

    async def buscar_contexto(
        self,
        query: str,
        *,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[ChunkNormativo]:
        filtrados = [c for c in self._chunks if c.score >= threshold][:top_k]
        return filtrados


class TestValidarAncoraNormativaRag:
    """Cenários de ``validar_ancora_normativa_rag``."""

    @pytest.mark.asyncio
    async def test_aceita_quando_melhor_score_acima_do_threshold(self) -> None:
        port = _PortFake(
            [ChunkNormativo(texto="Trecho LC 214", score=0.91, fonte="LC 214/2025")],
        )
        v = await validar_ancora_normativa_rag(
            "texto sem regex explícita",
            port,
            threshold=0.65,
        )
        assert v.aceito
        assert v.citacoes

    @pytest.mark.asyncio
    async def test_rejeita_quando_sem_chunks(self) -> None:
        port = _PortFake([])
        v = await validar_ancora_normativa_rag("algo", port, threshold=0.65)
        assert not v.aceito
        assert v.motivo == "sem_chunks_recuperados"

    @pytest.mark.asyncio
    async def test_rejeita_quando_score_abaixo_do_threshold(self) -> None:
        port = _PortFake([ChunkNormativo(texto="fraco", score=0.2, fonte="x")])
        v = await validar_ancora_normativa_rag("algo", port, threshold=0.65)
        assert not v.aceito
        assert v.motivo == "score_abaixo_threshold"

    @pytest.mark.asyncio
    async def test_texto_vazio_retorna_motivo_texto_vazio(self) -> None:
        port = _PortFake([])
        v = await validar_ancora_normativa_rag("  ", port, threshold=0.65)
        assert not v.aceito
        assert v.motivo == "texto_vazio"


class TestFiltrarRespostaRecomendacaoLlm:
    """Integração regex vs RAG em ``filtrar_resposta_recomendacao_llm``."""

    @pytest.mark.asyncio
    async def test_sem_port_usa_regex(self) -> None:
        out = await filtrar_resposta_recomendacao_llm(
            "Revisar plano conforme LC 214/2025.",
            base_normativa_port=None,
        )
        assert "LC 214/2025" in out

    @pytest.mark.asyncio
    async def test_com_port_rag_pode_aceitar_sem_ancora_regex(self) -> None:
        port = _PortFake(
            [ChunkNormativo(texto="contexto lc214", score=0.95, fonte="LC 214/2025")],
        )
        out = await filtrar_resposta_recomendacao_llm(
            "Melhore governança tributária gradualmente.",
            base_normativa_port=port,
            rag_threshold=0.5,
        )
        assert "Melhore governança" in out

    @pytest.mark.asyncio
    async def test_texto_vazio_retorna_mensagem_rejeicao(self) -> None:
        out = await filtrar_resposta_recomendacao_llm(
            "   ",
            base_normativa_port=None,
        )
        assert out == mensagem_rejeicao_guardrail()

    @pytest.mark.asyncio
    async def test_rag_rejeita_mas_regex_salva_com_ancora(self) -> None:
        port = _PortFake([ChunkNormativo(texto="fraco", score=0.1, fonte="x")])
        texto = "Planejar transição conforme LC 214/2025."
        out = await filtrar_resposta_recomendacao_llm(
            texto,
            base_normativa_port=port,
            rag_threshold=0.65,
        )
        assert out == texto.strip()

    @pytest.mark.asyncio
    async def test_erro_no_rag_cai_no_fallback_regex(self) -> None:
        class _PortQuebra(BaseNormativaPort):
            async def buscar_contexto(
                self,
                query: str,
                *,
                top_k: int = 3,
                threshold: float = 0.0,
            ) -> list[ChunkNormativo]:
                raise RuntimeError("falha pgvector fictícia")

        texto = "Ver LC 214/2025."
        out = await filtrar_resposta_recomendacao_llm(
            texto,
            base_normativa_port=_PortQuebra(),
        )
        assert out == texto

    @pytest.mark.asyncio
    async def test_erro_no_rag_sem_regex_retorna_rejeicao(self) -> None:
        class _PortQuebra(BaseNormativaPort):
            async def buscar_contexto(
                self,
                query: str,
                *,
                top_k: int = 3,
                threshold: float = 0.0,
            ) -> list[ChunkNormativo]:
                raise RuntimeError("indisponível")

        out = await filtrar_resposta_recomendacao_llm(
            "Texto sem referência normativa reconhecível.",
            base_normativa_port=_PortQuebra(),
        )
        assert out == mensagem_rejeicao_guardrail()
