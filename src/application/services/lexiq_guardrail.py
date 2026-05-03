"""
Guardrail mínimo Lexiq / Tributiq — texto deve exibir âncora normativa reconhecível.

Camada: Application (regra de produto; sem dependência de infraestrutura de LLM).
Analogia: como uma constraint Oracle que impede INSERT sem FK válida — aqui sem fonte, não publicamos.

Extensão RAG-light: validação semântica opcional via ``BaseNormativaPort``; regex permanece fallback (S11.9).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo

logger = structlog.get_logger(__name__)

# Padrões amplos porém objetivos (S02 protótipo — evolução: IDs Lexiq versionados).
_PADROES_ANCORA = (
    re.compile(r"LC\s*214/2025"),
    re.compile(r"EC\s*132/2023"),
    re.compile(r"ABNT\s*NBR\s*17301"),
    re.compile(r"ABNT\s*NBR\s*ISO\s*37301", re.I),
    re.compile(r"NT\s*2025\.00[0-9]", re.I),
    re.compile(r"LC\s*225/2026"),
)


def texto_tem_ancora_normativa(texto: str) -> bool:
    """Retorna True se houver ao menos uma referência normativa detectável."""
    if not texto or not str(texto).strip():
        return False
    t = str(texto).strip()
    return any(p.search(t) for p in _PADROES_ANCORA)


def mensagem_rejeicao_guardrail() -> str:
    """Texto estável devolvido ao usuário quando a IA não cita base reconhecível."""
    return (
        "Recomendação não exibida: o texto gerado não continha âncora normativa verificável "
        "(ex.: LC 214/2025, EC 132/2023, ABNT NBR 17301:2026). "
        "Princípio Tributiq (Lexiq): sem citação válida, a resposta é rejeitada."
    )


@dataclass(frozen=True, slots=True)
class ValidacaoLexiq:
    """Resultado da validação RAG + threshold."""

    aceito: bool
    motivo: str | None = None
    citacoes: tuple[ChunkNormativo, ...] = ()


async def validar_ancora_normativa_rag(
    texto: str,
    port: BaseNormativaPort,
    *,
    threshold: float = 0.65,
    top_k: int = 3,
) -> ValidacaoLexiq:
    """
    Usa similaridade do texto gerado com chunks na base pgvector.

    Se não houver chunks ou melhor score abaixo do threshold → não aceito (fallback pode usar regex).
    """
    q = (texto or "").strip()[:500]
    if not q:
        return ValidacaoLexiq(aceito=False, motivo="texto_vazio")

    chunks = await port.buscar_contexto(q, top_k=top_k, threshold=0.0)
    if not chunks:
        return ValidacaoLexiq(aceito=False, motivo="sem_chunks_recuperados")

    melhor = float(chunks[0].score)
    if melhor < float(threshold):
        return ValidacaoLexiq(aceito=False, motivo="score_abaixo_threshold")

    cit = tuple(chunks[:top_k])
    return ValidacaoLexiq(aceito=True, citacoes=cit)


async def filtrar_resposta_recomendacao_llm(
    texto: str,
    *,
    base_normativa_port: BaseNormativaPort | None,
    rag_threshold: float = 0.65,
) -> str:
    """
    Pós-processamento único para adapters LLM: RAG opcional + fallback regex Lexiq.
    """
    out = (texto or "").strip()
    if not out:
        return mensagem_rejeicao_guardrail()

    if base_normativa_port is not None:
        try:
            validado = await validar_ancora_normativa_rag(
                out,
                base_normativa_port,
                threshold=rag_threshold,
            )
            if validado.aceito:
                return out
            logger.info(
                "lexiq_guardrail_rag_rejeitou",
                motivo=validado.motivo,
                usa_fallback_regex=True,
            )
        except Exception as exc:
            logger.warning("lexiq_guardrail_rag_erro", erro=str(exc), exc_info=True)

    if texto_tem_ancora_normativa(out):
        return out
    return mensagem_rejeicao_guardrail()
