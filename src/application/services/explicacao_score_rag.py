"""
Recuperação RAG para narrativa «explicação do score» (Onda IA 1.1 — Fase E).

Camada: Application
Monta consulta semântica, serializa chunks para prompt/UI e mapeia ``EvidenceRef``.
"""

from __future__ import annotations

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo
from src.domain.value_objects.evidence_ref import EvidenceRef

_RAG_STATUS_COM_FONTE = "com_fonte"
_RAG_STATUS_INSUFICIENTE = "base_insuficiente"
_RAG_STATUS_NAO_RECUPERADO = "nao_recuperado"


def montar_query_rag_explicacao_score(
    score_geral: float,
    campos_extras: dict[str, object],
) -> str:
    """Consulta semântica alinhada ao diagnóstico (produto + norma reforma consumo)."""
    partes: list[str] = [
        "QualiDiagIQ diagnóstico tributário reforma consumo CBS IBS",
        f"score maturidade {score_geral}",
    ]
    dim = campos_extras.get("dimensao_mais_critica")
    if isinstance(dim, str) and dim.strip():
        partes.append(f"dimensão prioritária {dim.strip()}")
    setor = campos_extras.get("empresa_setor_macro")
    if isinstance(setor, str) and setor.strip():
        partes.append(f"setor {setor.strip()}")
    regime = campos_extras.get("empresa_regime")
    if isinstance(regime, str) and regime.strip():
        partes.append(f"regime {regime.strip()}")
    partes.append("LC 214/2025 EC 132/2023 ABNT NBR 17301")
    return " ".join(partes)[:500]


def formatar_rag_contexto_para_prompt(chunks: list[ChunkNormativo]) -> str:
    """Bloco citável injetado no prompt da explicação do score."""
    if not chunks:
        return ""
    linhas = [
        "TRECHOS RECUPERADOS DA BASE DE CONHECIMENTO (use apenas como apoio; não invente dispositivo):",
    ]
    for i, ch in enumerate(chunks, start=1):
        ref = ch.artigo or ch.fonte or f"fonte-{i}"
        linhas.append(f"[{i}] ({ch.fonte} | {ref} | relevância {ch.score:.2f})")
        linhas.append(ch.texto.strip()[:1200])
        linhas.append("")
    return "\n".join(linhas).strip()


def chunks_para_evidencias(chunks: list[ChunkNormativo]) -> tuple[EvidenceRef, ...]:
    """Converte chunks recuperados em evidências rastreáveis (guardrail / auditoria)."""
    out: list[EvidenceRef] = []
    for ch in chunks[:4]:
        dispositivo = (ch.artigo or ch.fonte or "trecho").strip()
        out.append(
            EvidenceRef(
                fonte=ch.fonte.strip() or "Lexiq",
                titulo=dispositivo,
                dispositivo=dispositivo,
            )
        )
    return tuple(out)


def chunks_para_fontes_rag(chunks: list[ChunkNormativo]) -> tuple[dict[str, object], ...]:
    """Serialização estável para JSONB e UI."""
    registos: list[dict[str, object]] = []
    for ch in chunks[:6]:
        texto = ch.texto.strip()
        trecho = texto[:280] + ("…" if len(texto) > 280 else "")
        registos.append(
            {
                "fonte": ch.fonte,
                "dispositivo": ch.artigo,
                "score": round(float(ch.score), 4),
                "trecho": trecho,
            }
        )
    return tuple(registos)


def determinar_rag_status(
    chunks: list[ChunkNormativo],
    *,
    threshold: float,
) -> str:
    """Classifica se a recuperação atingiu confiança mínima."""
    if not chunks:
        return _RAG_STATUS_NAO_RECUPERADO
    if float(chunks[0].score) >= float(threshold):
        return _RAG_STATUS_COM_FONTE
    return _RAG_STATUS_INSUFICIENTE


async def recuperar_contexto_explicacao_score(
    port: BaseNormativaPort,
    score_geral: float,
    campos_extras: dict[str, object],
    *,
    top_k: int = 4,
    threshold: float = 0.65,
) -> tuple[list[ChunkNormativo], str, tuple[EvidenceRef, ...]]:
    """
    Busca chunks normativos/produto e devolve status + evidências.

    Returns:
        (chunks, rag_status, evidencias)
    """
    query = montar_query_rag_explicacao_score(score_geral, campos_extras)
    chunks = await port.buscar_contexto(query, top_k=top_k, threshold=0.0)
    status = determinar_rag_status(chunks, threshold=threshold)
    evidencias = chunks_para_evidencias(chunks) if chunks else ()
    return chunks, status, evidencias
