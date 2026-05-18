"""
Adapter pgvector + embeddings OpenAI para ``BaseNormativaPort``.

Camada: Infrastructure
Similaridade: operador ``<=>`` (cosine distance) — score ≈ ``1 - distância`` para vetores normalizados.
"""

from __future__ import annotations

import asyncpg
import httpx
import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo
from src.infrastructure.rag.catalogo_fontes_index import resolver_entrada_por_caminho

logger = structlog.get_logger(__name__)


def _vetor_para_sql_literal(vec: list[float]) -> str:
    return "[" + ",".join(str(float(x)) for x in vec) + "]"


async def _embedding_openai(
    texto: str,
    *,
    api_key: str,
    model: str,
    timeout_seconds: float = 60.0,
) -> list[float]:
    """Chama OpenAI Embeddings API (REST) — dimensão deve coincidir com migração 0020."""
    limpo = (texto or "").strip()
    if not limpo:
        raise ValueError("Texto vazio para embedding.")
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        res = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={"model": model, "input": limpo[:8000]},
        )
        res.raise_for_status()
        body = res.json()
        data = body.get("data")
        if not isinstance(data, list) or not data:
            raise RuntimeError("Resposta OpenAI embeddings sem data.")
        emb = data[0].get("embedding")
        if not isinstance(emb, list):
            raise RuntimeError("embedding inválido na resposta OpenAI.")
        return [float(x) for x in emb]


class PgvectorBaseNormativaAdapter(BaseNormativaPort):
    """Leitura asyncpg em ``qdi_rag.documento_normativo``."""

    def __init__(
        self,
        dsn: str,
        openai_api_key: str,
        *,
        embedding_model: str = "text-embedding-3-small",
        connect_timeout_seconds: float = 10.0,
    ) -> None:
        self._dsn = dsn.strip().replace("postgresql+asyncpg://", "postgresql://", 1)
        self._openai_api_key = openai_api_key.strip()
        self._embedding_model = embedding_model.strip()
        self._connect_timeout = connect_timeout_seconds

    async def buscar_contexto(
        self,
        query: str,
        *,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[ChunkNormativo]:
        q = (query or "").strip()
        if not q:
            return []
        try:
            vec = await _embedding_openai(
                q,
                api_key=self._openai_api_key,
                model=self._embedding_model,
            )
        except Exception as exc:
            logger.warning("rag_embedding_openai_falhou", erro=str(exc), exc_info=True)
            return []

        literal = _vetor_para_sql_literal(vec)
        conn = await asyncpg.connect(self._dsn, timeout=self._connect_timeout)
        try:
            rows = await conn.fetch(
                """
                SELECT fonte, artigo, texto,
                       (1 - (embedding <=> $1::vector))::double precision AS score
                FROM qdi_rag.documento_normativo
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                literal,
                max(1, min(int(top_k), 50)),
            )
        except Exception as exc:
            logger.warning("rag_pgvector_busca_falhou", erro=str(exc), exc_info=True)
            return []
        finally:
            await conn.close()

        out: list[ChunkNormativo] = []
        for row in rows:
            score = float(row["score"])
            if score < float(threshold):
                continue
            fonte_raw = str(row["fonte"])
            artigo_raw = str(row["artigo"]) if row["artigo"] is not None else None
            ent = resolver_entrada_por_caminho(artigo_raw or "")
            catalogo_id = fonte_raw if fonte_raw.startswith("FONTE-") else (ent.id if ent else fonte_raw)
            classe = ent.classe if ent else None
            out.append(
                ChunkNormativo(
                    texto=str(row["texto"]),
                    score=score,
                    fonte=catalogo_id,
                    artigo=artigo_raw,
                    catalogo_id=catalogo_id,
                    classe=classe,
                )
            )
        return out
