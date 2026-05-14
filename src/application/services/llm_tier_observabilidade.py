"""
Resolução de tier LLM só para **observabilidade** (logs).

Camada: Application — puro; não altera ``QDI_LLM_BACKEND`` (ADR-021, plano hardening 2.3.1).

Precedência quando todos os inputs estão disponíveis no mesmo ponto de chamada:
1. ``tier_use_case`` (ex.: plano do diagnóstico);
2. claim JWT assinada ``qdi_llm_tier`` (``local`` | ``standard`` | ``premium``);
3. mapeamento de ``perfil_conta`` do JWT (``gratuito`` → local, ``avancado`` → standard, ``admin`` → premium);
4. ``QDI_LLM_DEFAULT_TIER`` (Settings);
5. fallback por ``APP_ENV``: ``standard`` em ``production``, senão ``local``.

Analogia (Winthor): ordem de precedência de parâmetros na filial — o primeiro explícito ganha;
aqui o «explícito» é o que vem do caso de uso ou do token assinado, nunca de header HTTP público.
"""

from __future__ import annotations

from typing import Literal

LlmObsTier = Literal["local", "standard", "premium"]

_VALID_TIERS: frozenset[str] = frozenset({"local", "standard", "premium"})


def _normalizar_tier_literal(raw: str | None) -> LlmObsTier | None:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in _VALID_TIERS:
        return s  # type: ignore[return-value]
    return None


def tier_observabilidade_de_plano_str(plano: str | None) -> LlmObsTier | None:
    """
    Mapeia string de plano (wizard / painel) para tier de log.

    Domínio actual: ``gratuito`` / ``avancado``; strings futuras toleradas sem falhar.
    """
    if plano is None:
        return None
    p = str(plano).strip().lower()
    if p in ("avancado", "plus", "pro", "enterprise"):
        return "standard"
    if p in ("gratuito", "free", "gratis"):
        return "local"
    return None


def tier_observabilidade_de_perfil_conta(perfil: str | None) -> LlmObsTier | None:
    """Deriva tier de observabilidade do claim ``perfil_conta`` do JWT painel (assinado)."""
    if perfil is None:
        return None
    p = str(perfil).strip().lower()
    if p == "admin":
        return "premium"
    if p == "avancado":
        return "standard"
    if p == "gratuito":
        return "local"
    return None


def _fallback_ambiente_app_env(app_env: str) -> LlmObsTier:
    return "standard" if str(app_env).strip().lower() == "production" else "local"


def resolver_tier_efetivo_observabilidade(
    *,
    tier_use_case: str | None,
    tier_jwt_claim: str | None,
    perfil_conta_jwt: str | None,
    settings_default_tier: str,
    app_env: str,
) -> tuple[LlmObsTier, str]:
    """
    Calcula tier efectivo e etiqueta da fonte vencedora (para ``structlog``).

    Returns:
        Tupla ``(tier, tier_fonte)`` com ``tier_fonte`` ∈
        ``use_case`` | ``jwt_claim_qdi_llm_tier`` | ``jwt_perfil_conta`` |
        ``settings_qdi_llm_default_tier`` | ``app_env_fallback``.
    """
    t_uc = _normalizar_tier_literal(tier_use_case)
    if t_uc is not None:
        return t_uc, "use_case"
    t_claim = _normalizar_tier_literal(tier_jwt_claim)
    if t_claim is not None:
        return t_claim, "jwt_claim_qdi_llm_tier"
    t_pf = tier_observabilidade_de_perfil_conta(perfil_conta_jwt)
    if t_pf is not None:
        return t_pf, "jwt_perfil_conta"
    t_set = _normalizar_tier_literal(settings_default_tier)
    if t_set is not None:
        return t_set, "settings_qdi_llm_default_tier"
    return _fallback_ambiente_app_env(app_env), "app_env_fallback"
