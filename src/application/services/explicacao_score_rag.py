"""
Recuperação RAG para narrativa «explicação do score» (Onda IA 1.1 — Fase E).

Camada: Application
Monta consulta semântica, serializa chunks para prompt/UI e mapeia ``EvidenceRef``.
"""

from __future__ import annotations

from src.application.ports.base_normativa_port import BaseNormativaPort, ChunkNormativo
from src.domain.ports.llm_gateway import LlmGatewayResponse
from src.domain.value_objects.evidence_ref import EvidenceRef

RAG_STATUS_COM_FONTE = "com_fonte"
RAG_STATUS_INSUFICIENTE = "base_insuficiente"
RAG_STATUS_NAO_RECUPERADO = "nao_recuperado"

MENSAGEM_BASE_NORMATIVA_INSUFICIENTE = (
    "Base normativa insuficiente para gerar explicação auditável. "
    "Reexecute após ingestão das fontes oficiais ou revise o corpus RAG."
)


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
        ref_id = ch.catalogo_id or ch.fonte or f"fonte-{i}"
        ref = ch.artigo or ref_id
        linhas.append(f"[{i}] ({ref_id} | {ref} | relevância {ch.score:.2f})")
        linhas.append(ch.texto.strip()[:1200])
        linhas.append("")
    return "\n".join(linhas).strip()


def chunks_para_evidencias(chunks: list[ChunkNormativo]) -> tuple[EvidenceRef, ...]:
    """Converte chunks recuperados em evidências rastreáveis (guardrail / auditoria)."""
    out: list[EvidenceRef] = []
    for ch in chunks[:4]:
        ref_id = (ch.catalogo_id or ch.fonte or "trecho").strip()
        dispositivo = (ch.artigo or ref_id).strip()
        out.append(
            EvidenceRef(
                fonte=ref_id or "Lexiq",
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
        ref_id = ch.catalogo_id or ch.fonte
        item: dict[str, object] = {
            "fonte": ref_id,
            "dispositivo": ch.artigo,
            "score": round(float(ch.score), 4),
            "trecho": trecho,
        }
        if ch.classe:
            item["classe"] = ch.classe
        registos.append(item)
    return tuple(registos)


def determinar_rag_status(
    chunks: list[ChunkNormativo],
    *,
    threshold: float,
) -> str:
    """Classifica se a recuperação atingiu confiança mínima."""
    if not chunks:
        return RAG_STATUS_NAO_RECUPERADO
    if float(chunks[0].score) >= float(threshold):
        return RAG_STATUS_COM_FONTE
    return RAG_STATUS_INSUFICIENTE


def rag_recuperacao_insuficiente(rag_status: str) -> bool:
    """True quando não há base citável suficiente (DP-006 — gate forte)."""
    return rag_status in (RAG_STATUS_INSUFICIENTE, RAG_STATUS_NAO_RECUPERADO)


def resposta_bloqueada_base_normativa_insuficiente(
    *,
    policy_version: str = "2026-05-15-v1",
) -> LlmGatewayResponse:
    """Resposta controlada sem chamar o LLM."""
    return LlmGatewayResponse(
        text=MENSAGEM_BASE_NORMATIVA_INSUFICIENTE,
        provider="none",
        model="none",
        policy_version=policy_version,
        blocked_by_guardrail=True,
        guardrail_reason="rag_base_insuficiente",
        guardrail_status="blocked",
        rag_status=RAG_STATUS_INSUFICIENTE,
        fontes_rag=(),
    )


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
