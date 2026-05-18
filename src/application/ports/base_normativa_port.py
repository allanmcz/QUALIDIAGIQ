"""
Port de recuperação de contexto normativo para RAG-light (pgvector).

Camada: Application (contrato — Dependency Inversion).

Implementações:
    ``StubBaseNormativaAdapter`` — sem dados / sem OPENAI_API_KEY (fallback regex no guardrail).
    ``PgvectorBaseNormativaAdapter`` — infrastructure/adapters/base_normativa_pgvector.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChunkNormativo:
    """Trecho recuperado da base normativa versionada."""

    texto: str
    score: float
    fonte: str = ""
    artigo: str | None = None
    #: ID do ``catalogo_fontes.yml`` (ex.: ``FONTE-020``) — DP-006.
    catalogo_id: str | None = None
    classe: str | None = None


class BaseNormativaPort(ABC):
    """Busca semântica sobre chunks normativos (cosine similarity no Postgres)."""

    @abstractmethod
    async def buscar_contexto(
        self,
        query: str,
        *,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[ChunkNormativo]:
        """
        Recupera até ``top_k`` chunks ordenados por similaridade.

        Args:
            query: Texto de consulta (ex.: trecho da resposta LLM ou perfil empresa).
            top_k: máximo de linhas retornadas antes do filtro por ``threshold``.
            threshold: similaridade mínima em [0,1] — descarta chunks abaixo.

        Returns:
            Lista ordenada do mais similar para o menos (após filtro).
        """
        ...
