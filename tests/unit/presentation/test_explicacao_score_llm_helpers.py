"""Testes de mapeamento HTTP da explicação score LLM persistida."""

from __future__ import annotations

from uuid import uuid4

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.presentation.api.routers.diagnostico_helpers import _explicacao_score_llm_para_http


def _diag_min() -> Diagnostico:
    return Diagnostico(
        tenant_id=uuid4(),
        empresa=EmpresaInfo(
            cnpj="12345678000195",
            razao_social="T",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        ),
        respondente=Respondente(email="a@b.com"),
    )


class TestExplicacaoScoreLlmParaHttp:
    """Cobertura de ramos do helper GET."""

    def test_retorna_none_sem_dict(self) -> None:
        d = _diag_min()
        d.explicacao_score_llm = None
        assert _explicacao_score_llm_para_http(d) is None

    def test_mapeia_snapshot_valido_sem_gerado_em(self) -> None:
        d = _diag_min()
        d.explicacao_score_llm = {
            "text": "ok",
            "provider": "p",
            "model": "m",
            "policy_version": "v",
            "blocked_by_guardrail": False,
            "guardrail_status": "ok",
        }
        out = _explicacao_score_llm_para_http(d)
        assert out is not None
        assert out.text == "ok"
        assert out.gerado_em is None

    def test_json_invalido_retorna_none(self) -> None:
        d = _diag_min()
        d.explicacao_score_llm = {
            "text": "ok",
            "provider": "p",
            "model": "m",
            "policy_version": "v",
            "input_tokens": "nao-numero",
        }
        assert _explicacao_score_llm_para_http(d) is None

    def test_gratuito_omite_snapshot_mesmo_persistido(self) -> None:
        d = _diag_min()
        d.plano = PlanoDiagnostico.GRATUITO
        d.explicacao_score_llm = {
            "text": "secreto",
            "provider": "p",
            "model": "m",
            "policy_version": "v",
            "blocked_by_guardrail": False,
            "guardrail_status": "ok",
        }
        assert _explicacao_score_llm_para_http(d, perfil_conta="gratuito") is None

    def test_avancado_mapeia_snapshot(self) -> None:
        d = _diag_min()
        d.explicacao_score_llm = {
            "text": "ok",
            "provider": "p",
            "model": "m",
            "policy_version": "v",
            "blocked_by_guardrail": False,
            "guardrail_status": "ok",
        }
        out = _explicacao_score_llm_para_http(d, perfil_conta="avancado")
        assert out is not None
        assert out.text == "ok"
