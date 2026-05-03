"""
Stub do port normativo — sem embedding / sem tabela populada.

Camada: Infrastructure
"""

from __future__ import annotations

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo


class StubBaseNormativaAdapter(BaseNormativaPort):
    """Retorna vazio; guardrail Lexiq usa regex de emergência."""

    async def buscar_contexto(
        self,
        query: str,
        *,
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> list[ChunkNormativo]:
        del query, top_k, threshold
        return []
