"""
Regras de acesso à explicação LLM do score no painel (tier / plano).

Camada: Application
Produto: narrativa Plus/Pro — perfil ``avancado`` ou ``admin``, ou diagnóstico com plano avançado.
"""

from __future__ import annotations

from src.domain.entities.diagnostico import Diagnostico, PlanoDiagnostico

_MENSAGEM_403 = (
    "Explicação do score por IA está disponível no plano avançado da conta na plataforma "
    "(perfil avançado ou diagnóstico Plus). Faça upgrade para desbloquear."
)


def perfil_pode_explicacao_score_llm(perfil_conta: str) -> bool:
    """``perfil_conta`` vem do JWT (``gratuito`` | ``avancado`` | ``admin``)."""
    p = (perfil_conta or "").strip().lower()
    return p in ("avancado", "admin")


def diagnostico_elegivel_explicacao_score_llm(d: Diagnostico) -> bool:
    """Plano persistido do diagnóstico (``avancado`` = Plus/Pro no MVP)."""
    return d.plano == PlanoDiagnostico.AVANCADO


def pode_gerar_explicacao_score_llm(perfil_conta: str, diagnostico: Diagnostico) -> bool:
    """Combina perfil da sessão e plano do diagnóstico."""
    return perfil_pode_explicacao_score_llm(
        perfil_conta
    ) or diagnostico_elegivel_explicacao_score_llm(diagnostico)


def explicacao_score_llm_incluir_em_get(
    perfil_conta: str | None,
    diagnostico: Diagnostico,
) -> bool:
    """GET painel: omite JSONB quando sessão não tem tier (defesa além da UI)."""
    if perfil_conta is None:
        return True
    return pode_gerar_explicacao_score_llm(perfil_conta, diagnostico)


def mensagem_acesso_negado_explicacao_score_llm() -> str:
    return _MENSAGEM_403
