"""
RAG local via embeddings Ollama + ficheiros Markdown (sem pgvector).

Camada: Infrastructure — Onda IA 1.1 (Fase D/E em dev sem OPENAI_API_KEY).
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import httpx
import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo

logger = structlog.get_logger(__name__)

_MD_PILOTO_PADRAO: tuple[str, ...] = (
    "docs/refs/01_PRD_BASE.md",
    "docs/refs/02_MOSCOW_FEATURES.md",
    "docs/refs/04_METODOLOGIA.md",
    "docs/refs/05_QUESTIONARIO_v1.md",
)

_ADR_GLOB = ".github/adr/ADR-*.md"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _chunk_md(text: str, *, size: int = 800) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(buf) + len(p) + 2 > size and buf:
            chunks.append(buf.strip())
            buf = p
        else:
            buf = f"{buf}\n\n{p}".strip() if buf else p
    if buf:
        chunks.append(buf.strip())
    return chunks


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class _ChunkIndexado:
    __slots__ = ("artigo", "embedding", "fonte", "texto")

    def __init__(
        self,
        fonte: str,
        artigo: str,
        texto: str,
        embedding: list[float],
    ) -> None:
        self.fonte = fonte
        self.artigo = artigo
        self.texto = texto
        self.embedding = embedding


class OllamaLocalBaseNormativaAdapter(BaseNormativaPort):
    """
    Índice em memória sobre Markdown piloto + ADRs + cache JSON opcional (índice código).

    Analogia: materialized view em memória — rebuild lazy no primeiro ``buscar_contexto``.
    """

    def __init__(
        self,
        ollama_base_url: str,
        *,
        embedding_model: str = "mxbai-embed-large:latest",
        md_paths: tuple[str, ...] | None = None,
        incluir_adrs: bool = True,
        codigo_index_json: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self._embed_url = ollama_base_url.strip().rstrip("/") + "/api/embed"
        self._embedding_model = embedding_model.strip()
        self._md_paths = md_paths or _MD_PILOTO_PADRAO
        self._incluir_adrs = incluir_adrs
        self._codigo_index_json = (codigo_index_json or "").strip()
        self._timeout = timeout_seconds
        self._indice: list[_ChunkIndexado] | None = None

    async def _embedding_ollama(self, texto: str) -> list[float]:
        limpo = (texto or "").strip()[:2000]
        if not limpo:
            raise ValueError("Texto vazio para embedding Ollama.")
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            res = await client.post(
                self._embed_url,
                json={"model": self._embedding_model, "input": limpo},
            )
            res.raise_for_status()
            body = res.json()
        embs = body.get("embeddings")
        if isinstance(embs, list) and embs:
            return [float(x) for x in embs[0]]
        emb = body.get("embedding")
        if isinstance(emb, list):
            return [float(x) for x in emb]
        raise RuntimeError("Resposta Ollama /api/embed sem vetor.")

    def _carregar_ficheiros(self) -> list[tuple[str, str, str]]:
        """(fonte_id, artigo/caminho, texto_chunk)."""
        root = _repo_root()
        saida: list[tuple[str, str, str]] = []
        for rel in self._md_paths:
            path = root / rel
            if not path.is_file():
                logger.warning("rag_ollama_ficheiro_ausente", caminho=rel)
                continue
            fid = path.stem.upper().replace("-", "_")[:40]
            for chunk in _chunk_md(path.read_text(encoding="utf-8", errors="replace")):
                saida.append((fid, rel, chunk))
        if self._incluir_adrs:
            for path in sorted(root.glob(_ADR_GLOB)):
                rel = str(path.relative_to(root))
                fid = path.stem
                for chunk in _chunk_md(path.read_text(encoding="utf-8", errors="replace")):
                    saida.append((fid, rel, chunk))
        if self._codigo_index_json:
            cache = root / self._codigo_index_json
            if cache.is_file():
                import json

                try:
                    registos = json.loads(cache.read_text(encoding="utf-8"))
                    if isinstance(registos, list):
                        for item in registos:
                            if not isinstance(item, dict):
                                continue
                            fonte = str(item.get("fonte") or "CODIGO")
                            artigo = str(item.get("artigo") or item.get("caminho") or "")
                            texto = str(item.get("texto") or "").strip()
                            if texto:
                                saida.append((fonte, artigo, texto))
                except Exception as exc:
                    logger.warning(
                        "rag_ollama_cache_codigo_invalido",
                        caminho=self._codigo_index_json,
                        erro=str(exc),
                    )
        return saida

    async def _garantir_indice(self) -> list[_ChunkIndexado]:
        if self._indice is not None:
            return self._indice
        registos = self._carregar_ficheiros()
        indice: list[_ChunkIndexado] = []
        for fonte, artigo, texto in registos:
            try:
                emb = await self._embedding_ollama(texto)
            except Exception as exc:
                logger.warning(
                    "rag_ollama_embed_chunk_falhou",
                    fonte=fonte,
                    artigo=artigo,
                    erro=str(exc),
                )
                continue
            indice.append(_ChunkIndexado(fonte, artigo, texto, emb))
        self._indice = indice
        logger.info("rag_ollama_indice_pronto", chunks=len(indice))
        return indice

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
            q_emb = await self._embedding_ollama(q)
            indice = await self._garantir_indice()
        except Exception as exc:
            logger.warning("rag_ollama_busca_falhou", erro=str(exc), exc_info=True)
            return []
        if not indice:
            return []
        scored: list[tuple[float, _ChunkIndexado]] = []
        for ch in indice:
            scored.append((_cosine(q_emb, ch.embedding), ch))
        scored.sort(key=lambda x: x[0], reverse=True)
        limite = max(1, min(int(top_k), 50))
        out: list[ChunkNormativo] = []
        for score, ch in scored[:limite]:
            if score < float(threshold):
                continue
            out.append(
                ChunkNormativo(
                    texto=ch.texto,
                    score=float(score),
                    fonte=ch.fonte,
                    artigo=ch.artigo,
                )
            )
        return out
