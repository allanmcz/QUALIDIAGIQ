"""Testes do resolver de tier LLM (observabilidade — plano hardening 2.3.1)."""

from __future__ import annotations

import pytest

from src.application.services.llm_tier_observabilidade import (
    resolver_tier_efetivo_observabilidade,
    tier_observabilidade_de_perfil_conta,
    tier_observabilidade_de_plano_str,
)


class TestLlmTierObservabilidade:
    """Precedência use_case → JWT claim → perfil → settings → APP_ENV."""

    def test_use_case_vence_settings(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case="premium",
            tier_jwt_claim="local",
            perfil_conta_jwt="admin",
            settings_default_tier="local",
            app_env="production",
        )
        assert t == "premium"
        assert fonte == "use_case"

    def test_claim_jwt_vence_perfil_e_settings(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case=None,
            tier_jwt_claim="standard",
            perfil_conta_jwt="admin",
            settings_default_tier="local",
            app_env="development",
        )
        assert t == "standard"
        assert fonte == "jwt_claim_qdi_llm_tier"

    def test_perfil_admin_sem_claim(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case=None,
            tier_jwt_claim=None,
            perfil_conta_jwt="admin",
            settings_default_tier="local",
            app_env="development",
        )
        assert t == "premium"
        assert fonte == "jwt_perfil_conta"

    def test_settings_quando_sem_jwt(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case=None,
            tier_jwt_claim=None,
            perfil_conta_jwt=None,
            settings_default_tier="standard",
            app_env="development",
        )
        assert t == "standard"
        assert fonte == "settings_qdi_llm_default_tier"

    def test_fallback_producao_quando_settings_invalido(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case=None,
            tier_jwt_claim=None,
            perfil_conta_jwt=None,
            settings_default_tier="invalido_xyz",
            app_env="production",
        )
        assert t == "standard"
        assert fonte == "app_env_fallback"

    def test_fallback_dev_quando_settings_invalido(self) -> None:
        t, fonte = resolver_tier_efetivo_observabilidade(
            tier_use_case=None,
            tier_jwt_claim=None,
            perfil_conta_jwt=None,
            settings_default_tier="???",
            app_env="development",
        )
        assert t == "local"
        assert fonte == "app_env_fallback"

    @pytest.mark.parametrize(
        "plano,esperado",
        [
            ("gratuito", "local"),
            ("avancado", "standard"),
            ("plus", "standard"),
        ],
    )
    def test_plano_str(self, plano: str, esperado: str) -> None:
        assert tier_observabilidade_de_plano_str(plano) == esperado

    def test_perfil_desconhecido_retorna_none(self) -> None:
        assert tier_observabilidade_de_perfil_conta("xyz") is None

    def test_plano_none_retorna_none(self) -> None:
        assert tier_observabilidade_de_plano_str(None) is None

    def test_plano_desconhecido_retorna_none(self) -> None:
        assert tier_observabilidade_de_plano_str("plano_xyz") is None

    def test_perfil_none_retorna_none(self) -> None:
        assert tier_observabilidade_de_perfil_conta(None) is None

    def test_perfil_gratuito(self) -> None:
        assert tier_observabilidade_de_perfil_conta("gratuito") == "local"

    def test_perfil_avancado(self) -> None:
        assert tier_observabilidade_de_perfil_conta("avancado") == "standard"
