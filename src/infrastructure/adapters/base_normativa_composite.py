"""
Adapter composto — tenta várias fontes RAG e funde por score (Onda IA 1.1).

Camada: Infrastructure
"""

from __future__ import annotations

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo


class CompositeBaseNormativaAdapter(BaseNormativaPort):
    """Consulta adaptadores em sequência e devolve os melhores chunks únicos."""

    def __init__(self, *adapters: BaseNormativaPort) -> None:
        if not adapters:
            raise ValueError("CompositeBaseNormativaAdapter exige ao menos um adapter.")
        self._adapters = adapters

    async def buscar_contexto(
        self,
        query: str,
        *,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[ChunkNormativo]:
        vistos: set[tuple[str, str]] = set()
        fundidos: list[ChunkNormativo] = []
        for adapter in self._adapters:
            parcial = await adapter.buscar_contexto(
                query,
                top_k=max(top_k, 3),
                threshold=threshold,
            )
            for ch in parcial:
                chave = (ch.fonte, ch.texto[:96])
                if chave in vistos:
                    continue
                vistos.add(chave)
                fundidos.append(ch)
        fundidos.sort(key=lambda c: c.score, reverse=True)
        limite = max(1, min(int(top_k), 50))
        return fundidos[:limite]
