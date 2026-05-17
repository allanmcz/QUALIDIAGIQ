"""
Monta ``campos_extras`` para ``ExplicarScoreLlmUseCase`` (contexto rico ao gateway).

Camada: Application
"""

from __future__ import annotations

from typing import Any

from src.application.services.explicacao_score_llm_saida import parecer_explicacao_score_substantivo
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import Dimensao, NivelMaturidade

_ROTULO_DIMENSAO_PT: dict[str, str] = {
    Dimensao.FISCAL.value: "Fiscal",
    Dimensao.ESTRATEGICA.value: "Estratégica",
    Dimensao.CONTABIL.value: "Contábil",
    Dimensao.FINANCEIRA.value: "Financeira",
    Dimensao.OPERACIONAL.value: "Operacional",
    Dimensao.TECNOLOGICA.value: "Tecnológica",
    Dimensao.COMPLIANCE_ABNT.value: "Compliance ABNT 17301",
}


def montar_campos_extras_explicacao_score(d: Diagnostico) -> dict[str, object]:
    """Score por dimensão + metadados empresa - sem recalcular o motor 0-100."""
    extras: dict[str, object] = {
        "empresa_razao_social": d.empresa.razao_social,
        "empresa_porte": d.empresa.porte.value,
        "empresa_regime": d.empresa.regime.value,
        "empresa_setor_macro": d.empresa.setor_macro.value,
        "empresa_uf": d.empresa.uf,
        "diagnostico_id": str(d.id),
    }
    if d.empresa.faixa_faturamento is not None:
        extras["empresa_faixa_faturamento"] = d.empresa.faixa_faturamento.value
    if d.score_geral is not None:
        extras["nivel_maturidade"] = NivelMaturidade.from_score(float(d.score_geral)).value
    snap = d.score_completo_snapshot
    if snap is not None:
        extras["score_por_dimensao"] = {
            dim.value: sn.valor for dim, sn in snap.score_por_dimensao.items()
        }
        extras["pesos_por_dimensao"] = {
            dim.value: sn.peso_total_aplicado for dim, sn in snap.score_por_dimensao.items()
        }
        dim_critica, valor_critico = min(
            snap.score_por_dimensao.items(),
            key=lambda item: item[1].valor,
        )
        extras["dimensao_mais_critica"] = _ROTULO_DIMENSAO_PT.get(
            dim_critica.value,
            dim_critica.value,
        )
        extras["score_dimensao_mais_critica"] = valor_critico.valor
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
    blocked = out.blocked_by_guardrail
    reason = out.guardrail_reason
    status = out.guardrail_status
    if not blocked and not parecer_explicacao_score_substantivo(out.text):
        blocked = True
        reason = reason or "parecer_nao_substantivo"
        status = "blocked"
    return {
        "text": out.text,
        "provider": out.provider,
        "model": out.model,
        "policy_version": out.policy_version,
        "input_tokens": out.input_tokens,
        "output_tokens": out.output_tokens,
        "estimated_cost_usd": out.estimated_cost_usd,
        "latency_ms": out.latency_ms,
        "blocked_by_guardrail": blocked,
        "guardrail_reason": reason,
        "guardrail_status": status,
        "gerado_em": gerado_em_iso,
        "trace_id": trace_id,
    }
