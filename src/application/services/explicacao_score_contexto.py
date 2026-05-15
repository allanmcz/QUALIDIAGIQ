"""
Monta ``campos_extras`` para ``ExplicarScoreLlmUseCase`` (contexto rico ao gateway).

Camada: Application
"""

from __future__ import annotations

from typing import Any

from src.domain.entities.diagnostico import Diagnostico


def montar_campos_extras_explicacao_score(d: Diagnostico) -> dict[str, object]:
    """Score por dimensão + metadados empresa - sem recalcular o motor 0-100."""
    extras: dict[str, object] = {
        "empresa_porte": d.empresa.porte.value,
        "empresa_regime": d.empresa.regime.value,
        "empresa_setor_macro": d.empresa.setor_macro.value,
        "empresa_uf": d.empresa.uf,
        "diagnostico_id": str(d.id),
    }
    if d.empresa.faixa_faturamento is not None:
        extras["empresa_faixa_faturamento"] = d.empresa.faixa_faturamento.value
    snap = d.score_completo_snapshot
    if snap is not None:
        extras["score_por_dimensao"] = {
            dim.value: sn.valor for dim, sn in snap.score_por_dimensao.items()
        }
        extras["pesos_por_dimensao"] = {
            dim.value: sn.peso_total_aplicado for dim, sn in snap.score_por_dimensao.items()
        }
    return extras


def snapshot_explicacao_score_llm_de_resposta(
    out: object,
    *,
    trace_id: str,
    gerado_em_iso: str,
) -> dict[str, Any]:
    """Serializa ``LlmGatewayResponse`` (ou equivalente) para JSONB."""
    from src.domain.ports.llm_gateway import LlmGatewayResponse

    if not isinstance(out, LlmGatewayResponse):
        raise TypeError("Resposta deve ser LlmGatewayResponse")
    return {
        "text": out.text,
        "provider": out.provider,
        "model": out.model,
        "policy_version": out.policy_version,
        "input_tokens": out.input_tokens,
        "output_tokens": out.output_tokens,
        "estimated_cost_usd": out.estimated_cost_usd,
        "latency_ms": out.latency_ms,
        "blocked_by_guardrail": out.blocked_by_guardrail,
        "guardrail_reason": out.guardrail_reason,
        "guardrail_status": out.guardrail_status,
        "gerado_em": gerado_em_iso,
        "trace_id": trace_id,
    }
