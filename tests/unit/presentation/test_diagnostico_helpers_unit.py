"""Testes unitários puros de ``diagnostico_helpers`` (sem HTTP)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.presentation.api.routers.diagnostico_helpers import (
    _aceite_lgpd_para_http,
    _campos_auditoria_http,
    _checklist_m12_para_http,
    _conclusao_publica_row_para_schema,
    _enviar_otp_verificacao_para_email,
    _executar_criar_diagnostico_core,
    _mascarar_email_norm,
    _parse_if_match_versao,
    _payload_json_como_dict,
    _plano_efetivo_para_criacao,
    _quadro_implantacao_para_http,
    _score_completo_para_http,
)
from src.presentation.api.schemas import IniciarDiagnosticoRequest


def _diag() -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Empresa X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="6201500",
        uf="SP",
        setor_macro=SetorMacro.SERVICOS,
    )
    d = Diagnostico(
        tenant_id=uuid4(),
        empresa=empresa,
        respondente=Respondente(email="resp@x.com"),
        plano=PlanoDiagnostico.GRATUITO,
    )
    d.finalizar(70.0)
    d.score_completo_snapshot = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )
    return d


def test_payload_json_como_dict_variantes() -> None:
    assert _payload_json_como_dict(None) is None
    assert _payload_json_como_dict({"a": 1}) == {"a": 1}
    assert _payload_json_como_dict('{"a":1}') == {"a": 1}
    assert _payload_json_como_dict("[1,2]") is None
    assert _payload_json_como_dict("{invalido}") is None
    assert _payload_json_como_dict(123) is None


def test_mascarar_email_norm() -> None:
    assert _mascarar_email_norm("a@x.com") == "*@x.com"
    assert _mascarar_email_norm("abc@x.com") == "a***@x.com"
    assert _mascarar_email_norm("sem-arroba") == "***"


def test_campos_checklist_quadro_aceite_para_http() -> None:
    d = _diag()
    d.hash_evidencia = "a" * 64
    d.versao_otimista = 3
    d.checklist_m12_estado = [1] * 10
    d.quadro_implantacao_anotacoes = {"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}}
    d.aceite_termos_privacidade_em = datetime.now(UTC)

    assert _campos_auditoria_http(d) == ("a" * 64, 3)
    assert _checklist_m12_para_http(d) == [1] * 10
    assert _quadro_implantacao_para_http(d) == {"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}}
    assert _aceite_lgpd_para_http(d) is not None

    d.checklist_m12_estado = [9] * 10
    d.aceite_termos_privacidade_em = "nao-datetime"  # type: ignore[assignment]
    assert _checklist_m12_para_http(d) is None
    assert _aceite_lgpd_para_http(d) is None


def test_score_completo_para_http_valido_e_none() -> None:
    d = _diag()
    score = _score_completo_para_http(d)
    assert score is not None
    assert score.score_geral.valor == 70.0
    d.score_completo_snapshot = None
    assert _score_completo_para_http(d) is None


def test_conclusao_publica_row_para_schema_com_fallbacks() -> None:
    row = {
        "id": str(uuid4()),
        "status": "finalizado",
        "empresa_razao_social": "X",
        "locale_relatorio": "   ",
        "score_completo": {"invalido": True},
    }
    out = _conclusao_publica_row_para_schema(row)
    assert out.score_geral is None
    assert out.scores_por_dimensao == []
    assert out.locale_relatorio == "pt-BR"


@pytest.mark.asyncio
async def test_enviar_otp_verificacao_para_email_fluxos() -> None:
    fake_settings = SimpleNamespace(app_env="production")
    email_service = AsyncMock()
    email_service.enviar_codigo_verificacao_email.return_value = False

    with (
        patch(
            "src.presentation.api.routers.diagnostico_helpers.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "src.presentation.api.routers.diagnostico_helpers.codigo_store.pode_reenviar",
            return_value=True,
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await _enviar_otp_verificacao_para_email("a@x.com", email_service)
    assert exc.value.status_code == 503

    email_service.enviar_codigo_verificacao_email.return_value = True
    with (
        patch(
            "src.presentation.api.routers.diagnostico_helpers.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "src.presentation.api.routers.diagnostico_helpers.codigo_store.pode_reenviar",
            return_value=False,
        ),
        pytest.raises(HTTPException) as exc2,
    ):
        await _enviar_otp_verificacao_para_email("a@x.com", email_service)
    assert exc2.value.status_code == 429


def test_parse_if_match_variantes_e_erros() -> None:
    assert _parse_if_match_versao("3, 4") == 3
    assert _parse_if_match_versao('W/"9"') == 9
    with pytest.raises(ValueError, match="inteiro"):
        _parse_if_match_versao("abc")
    with pytest.raises(ValueError, match="inválida"):
        _parse_if_match_versao("0")


def test_plano_efetivo_para_criacao_regras_perfil() -> None:
    payload = IniciarDiagnosticoRequest.model_validate(
        {
            "empresa": {
                "cnpj": "",
                "razao_social": "Empresa",
                "porte": "micro",
                "regime": "simples_nacional",
                "cnae_principal": "1234567",
                "uf": "SP",
                "setor_macro": "comercio",
            },
            "respondente": {"email": "resp@x.com", "nome": "Resp"},
            "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 1}],
            "aceite_termos_privacidade": True,
            "plano": "AvANcaDo",
        }
    )
    assert _plano_efetivo_para_criacao(payload, None) == "gratuito"
    assert _plano_efetivo_para_criacao(payload, "gratuito") == "gratuito"
    assert _plano_efetivo_para_criacao(payload, "avancado") == "avancado"


@pytest.mark.asyncio
async def test_executar_criar_diagnostico_core_pergunta_nao_encontrada_e_value_error() -> None:
    payload = IniciarDiagnosticoRequest.model_validate(
        {
            "empresa": {
                "cnpj": "",
                "razao_social": "Empresa",
                "porte": "micro",
                "regime": "simples_nacional",
                "cnae_principal": "1234567",
                "uf": "SP",
                "setor_macro": "comercio",
            },
            "respondente": {"email": "resp@x.com", "nome": "Resp"},
            "respostas": [{"pergunta_id": str(uuid4()), "valor": 1}],
            "aceite_termos_privacidade": True,
        }
    )
    repo = AsyncMock()
    use_case = AsyncMock()

    with (
        patch(
            "src.presentation.api.routers.diagnostico_helpers.get_banco_perguntas_cached",
            return_value=[],
        ),
        pytest.raises(HTTPException) as exc,
    ):
        await _executar_criar_diagnostico_core(
            tenant_id=uuid4(),
            payload=payload,
            use_case=use_case,
            perfil_limite="gratuito",
            repo=repo,
        )
    assert exc.value.status_code == 400

    pergunta = SimpleNamespace(id=payload.respostas[0].pergunta_id)
    with patch(
        "src.presentation.api.routers.diagnostico_helpers.get_banco_perguntas_cached",
        return_value=[pergunta],
    ):
        use_case.execute.side_effect = ValueError("comando inválido")
        with pytest.raises(HTTPException) as exc2:
            await _executar_criar_diagnostico_core(
                tenant_id=uuid4(),
                payload=payload,
                use_case=use_case,
                perfil_limite="gratuito",
                repo=repo,
            )
    assert exc2.value.status_code == 400
