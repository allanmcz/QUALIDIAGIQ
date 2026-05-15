"""Testes de gate tier/plano para explicação LLM do score."""

from __future__ import annotations

import pytest

from src.application.services.explicacao_score_llm_acesso import (
    diagnostico_elegivel_explicacao_score_llm,
    explicacao_score_llm_incluir_em_get,
    mensagem_acesso_negado_explicacao_score_llm,
    perfil_pode_explicacao_score_llm,
    pode_gerar_explicacao_score_llm,
)
from src.application.services.explicacao_score_publica import (
    texto_explicacao_score_para_leitura_publica,
)
from src.domain.entities.diagnostico import PlanoDiagnostico
from tests.unit.presentation.test_api import _diag_finalizado_micro


class TestPerfilPodeExplicacaoScoreLlm:
    @pytest.mark.parametrize(
        "perfil,esperado", [("avancado", True), ("admin", True), ("gratuito", False), ("", False)]
    )
    def test_perfil(self, perfil: str, esperado: bool) -> None:
        assert perfil_pode_explicacao_score_llm(perfil) is esperado


class TestDiagnosticoElegivelExplicacao:
    def test_plano_avancado(self) -> None:
        d = _diag_finalizado_micro()
        d.plano = PlanoDiagnostico.AVANCADO
        assert diagnostico_elegivel_explicacao_score_llm(d) is True

    def test_plano_gratuito(self) -> None:
        d = _diag_finalizado_micro()
        d.plano = PlanoDiagnostico.GRATUITO
        assert diagnostico_elegivel_explicacao_score_llm(d) is False


class TestPodeGerarCombinado:
    def test_gratuito_com_plano_avancado(self) -> None:
        d = _diag_finalizado_micro()
        d.plano = PlanoDiagnostico.AVANCADO
        assert pode_gerar_explicacao_score_llm("gratuito", d) is True

    def test_negado(self) -> None:
        d = _diag_finalizado_micro()
        assert pode_gerar_explicacao_score_llm("gratuito", d) is False

    def test_mensagem_403(self) -> None:
        assert "plano avançado" in mensagem_acesso_negado_explicacao_score_llm().lower()


class TestExplicacaoScoreLlmIncluirEmGet:
    """GET painel omite JSONB quando tier negado."""

    def test_gratuito_sem_plano_avancado_omite(self) -> None:
        d = _diag_finalizado_micro()
        d.plano = PlanoDiagnostico.GRATUITO
        assert explicacao_score_llm_incluir_em_get("gratuito", d) is False

    def test_avancado_inclui(self) -> None:
        d = _diag_finalizado_micro()
        assert explicacao_score_llm_incluir_em_get("avancado", d) is True

    def test_gratuito_com_plano_avancado_inclui(self) -> None:
        d = _diag_finalizado_micro()
        d.plano = PlanoDiagnostico.AVANCADO
        assert explicacao_score_llm_incluir_em_get("gratuito", d) is True

    def test_perfil_none_inclui(self) -> None:
        d = _diag_finalizado_micro()
        assert explicacao_score_llm_incluir_em_get(None, d) is True


class TestTextoLeituraPublica:
    def test_none_quando_ausente(self) -> None:
        assert texto_explicacao_score_para_leitura_publica(None) is None

    def test_bloqueado_guardrail(self) -> None:
        assert (
            texto_explicacao_score_para_leitura_publica({"text": "x", "blocked_by_guardrail": True})
            is None
        )

    def test_texto_valido(self) -> None:
        assert texto_explicacao_score_para_leitura_publica({"text": "  narrativa  "}) == "narrativa"

    def test_texto_vazio(self) -> None:
        assert texto_explicacao_score_para_leitura_publica({"text": "   "}) is None

    def test_tipo_invalido(self) -> None:
        assert texto_explicacao_score_para_leitura_publica({"text": 1}) is None
