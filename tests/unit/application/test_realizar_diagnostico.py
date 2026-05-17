"""Testes unitários — ``RealizarDiagnostico`` (orquestração sem I/O real)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.application.ports.base_normativa_port import ChunkNormativo
from src.application.services.cnpj_consulta_service import ConsultaCnpjMaterializada
from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    RealizarDiagnostico,
)
from src.domain.entities.diagnostico import (
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.entities.questionario import Pergunta, TipoPergunta
from src.domain.ports.llm_gateway import LlmGatewayResponse
from src.domain.value_objects.llm_task_type import LlmTaskType
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)


def _pergunta_fiscal() -> Pergunta:
    return Pergunta(
        codigo="Q-FISC-T",
        dimensao=Dimensao.FISCAL,
        texto="Teste",
        peso=1.0,
        tipo=TipoPergunta.TERNARIA,
    )


def _empresa_com_cnpj() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="33014556000196",
        razao_social="ACME",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="4711302",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


def _plano_vazio() -> PlanoPainelSerializado:
    return PlanoPainelSerializado(
        versao_plano=1,
        checklist=(),
        matriz_impacto=(),
        cronograma=(),
    )


def _comando_base(
    *,
    aceite: bool = True,
    plano: str = "gratuito",
    force_refresh_cnpj: bool = False,
    empresa: EmpresaInfo | None = None,
) -> ComandoRealizarDiagnostico:
    p = _pergunta_fiscal()
    return ComandoRealizarDiagnostico(
        tenant_id=uuid4(),
        empresa=empresa or _empresa_com_cnpj(),
        respondente=Respondente(email="resp@teste.br", nome="Resp"),
        entradas_resposta=[
            EntradaRespostaDiagnostico(pergunta=p, valor_bruto="sim"),
        ],
        plano=plano,
        aceite_termos_privacidade=aceite,
        force_refresh_cnpj=force_refresh_cnpj,
    )


@pytest.fixture
def calcular_real() -> CalcularScoreUseCase:
    return CalcularScoreUseCase(normativa_repo=EmbutidasNormativaScoreMacroRepository())


@pytest.mark.asyncio
async def test_force_refresh_cnpj_sem_servico_levanta(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        cnpj_consulta_service=None,
    )
    cmd = _comando_base(force_refresh_cnpj=True)
    with pytest.raises(ValueError, match="force_refresh_cnpj"):
        await uc.execute(cmd)
    repo.salvar_e_materializar_plano_painel.assert_not_called()


@pytest.mark.asyncio
async def test_aceite_termos_false_levanta(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    uc = RealizarDiagnostico(repo=repo, calcular_score_use_case=calcular_real)
    cmd = _comando_base(aceite=False)
    with pytest.raises(ValueError, match="aceite dos termos"):
        await uc.execute(cmd)


@pytest.mark.asyncio
async def test_plano_desconhecido_cai_gratuito(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    uc = RealizarDiagnostico(repo=repo, calcular_score_use_case=calcular_real)
    cmd = _comando_base(plano="plano_inexistente_xyz")
    res = await uc.execute(cmd)
    assert res.diagnostico.plano == PlanoDiagnostico.GRATUITO


@pytest.mark.asyncio
async def test_llm_so_ancora_fixa_sem_port_normativa(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    llm = AsyncMock()
    llm.gerar_recomendacao = AsyncMock(return_value="Sugestão IA")
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_service=llm,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert res.recomendacao_ia == "Sugestão IA"
    llm.gerar_recomendacao.assert_awaited_once()
    ctx = llm.gerar_recomendacao.call_args.kwargs["base_normativa"]
    assert "EC 132/2023" in ctx
    assert "LC 214/2025" in ctx


@pytest.mark.asyncio
async def test_llm_com_port_sem_chunks_mantem_ancora(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    llm = AsyncMock()
    llm.gerar_recomendacao = AsyncMock(return_value="ok")
    norm = AsyncMock()
    norm.buscar_contexto = AsyncMock(return_value=[])
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_service=llm,
        base_normativa_port=norm,
    )
    await uc.execute(_comando_base())
    norm.buscar_contexto.assert_awaited_once()
    base = llm.gerar_recomendacao.call_args.kwargs["base_normativa"]
    assert "EC 132/2023" in base
    assert "trecho-rag" not in base


@pytest.mark.asyncio
async def test_llm_com_chunks_injeta_rag(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    llm = AsyncMock()
    llm.gerar_recomendacao = AsyncMock(return_value="ok")
    norm = AsyncMock()
    norm.buscar_contexto = AsyncMock(
        return_value=[ChunkNormativo(texto="trecho-rag LC 214", score=0.9, fonte="lexiq")]
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_service=llm,
        base_normativa_port=norm,
    )
    await uc.execute(_comando_base())
    base = llm.gerar_recomendacao.call_args.kwargs["base_normativa"]
    assert "trecho-rag LC 214" in base


@pytest.mark.asyncio
async def test_recomendacao_via_llm_gateway(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="Sugestão via gateway",
            provider="fake",
            model="fake-llm",
            policy_version="2026-05-15-v1",
        )
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert res.recomendacao_ia == "Sugestão via gateway"
    gw.complete.assert_awaited_once()
    req = gw.complete.call_args[0][0]
    assert req.task_type == LlmTaskType.RELATORIO_EXECUTIVO
    assert req.prompt_key == "recomendacao_pos_diagnostico"


@pytest.mark.asyncio
async def test_recomendacao_gateway_sem_trace_id_gera_trace_interno(
    calcular_real: CalcularScoreUseCase,
) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="ok",
            provider="fake",
            model="fake-llm",
            policy_version="v",
        )
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    cmd = replace(_comando_base(), trace_id=None)
    await uc.execute(cmd)
    req = gw.complete.call_args[0][0]
    assert len(req.trace_id) >= 8


@pytest.mark.asyncio
async def test_gateway_prevale_nao_chama_llm_service_quando_ambos(
    calcular_real: CalcularScoreUseCase,
) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="via gateway",
            provider="fake",
            model="fake-llm",
            policy_version="v",
        )
    )
    llm = AsyncMock()
    llm.gerar_recomendacao = AsyncMock(return_value="nunca")
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        llm_service=llm,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert res.recomendacao_ia == "via gateway"
    llm.gerar_recomendacao.assert_not_called()


@pytest.mark.asyncio
async def test_recomendacao_gateway_excecao_mensagem_estavel(
    calcular_real: CalcularScoreUseCase,
) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(side_effect=RuntimeError("falha rede"))
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert "indispon" in (res.recomendacao_ia or "").lower()


@pytest.mark.asyncio
async def test_recomendacao_gateway_bloqueado_mensagem_estavel(
    calcular_real: CalcularScoreUseCase,
) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="",
            provider="none",
            model="none",
            policy_version="v",
            blocked_by_guardrail=True,
            guardrail_reason="feature_disabled",
        )
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert "indispon" in (res.recomendacao_ia or "").lower()


@pytest.mark.asyncio
async def test_recomendacao_gateway_texto_vazio_mensagem_estavel(
    calcular_real: CalcularScoreUseCase,
) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="   \n",
            provider="fake",
            model="fake-llm",
            policy_version="v",
            blocked_by_guardrail=False,
        )
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert "indispon" in (res.recomendacao_ia or "").lower()


@pytest.mark.asyncio
async def test_recomendacao_gateway_adapter_exception_sem_flag_bloqueio(
    calcular_real: CalcularScoreUseCase,
) -> None:
    """Ramo do ``or`` em ``bloqueado`` quando só ``guardrail_reason`` indica excepção."""
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    gw = AsyncMock()
    gw.complete = AsyncMock(
        return_value=LlmGatewayResponse(
            text="deve ignorar",
            provider="x",
            model="y",
            policy_version="v",
            blocked_by_guardrail=False,
            guardrail_reason="adapter_exception",
        )
    )
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        llm_gateway=gw,
        base_normativa_port=None,
    )
    res = await uc.execute(_comando_base())
    assert "indispon" in (res.recomendacao_ia or "").lower()


@pytest.mark.asyncio
async def test_llm_gerar_recomendacao_excecao_mantem_diagnostico_com_mensagem_estavel(
    calcular_real: CalcularScoreUseCase,
) -> None:
    """Defesa em profundidade: falha do adapter não aborta o caso de uso."""
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    llm = AsyncMock()
    llm.gerar_recomendacao = AsyncMock(side_effect=RuntimeError("falha interna simulada"))
    uc = RealizarDiagnostico(repo=repo, calcular_score_use_case=calcular_real, llm_service=llm)
    res = await uc.execute(_comando_base())
    assert res.diagnostico is not None
    assert res.recomendacao_ia is not None
    assert "indispon" in res.recomendacao_ia.lower()


@pytest.mark.asyncio
async def test_pdf_storage_e_email_quando_configurado(calcular_real: CalcularScoreUseCase) -> None:
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    pdf = AsyncMock()
    pdf.gerar_pdf_diagnostico = AsyncMock(return_value=b"%PDF-1.4 fake")
    storage = AsyncMock()
    storage.upload_pdf = AsyncMock(return_value="https://storage.example/r.pdf")
    email = AsyncMock()
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        pdf_generator=pdf,
        storage_service=storage,
        email_service=email,
    )
    res = await uc.execute(_comando_base())
    assert res.relatorio_pdf_url == "https://storage.example/r.pdf"
    pdf.gerar_pdf_diagnostico.assert_awaited_once()
    storage.upload_pdf.assert_awaited_once()
    email.enviar_email_com_relatorio.assert_awaited_once()


@pytest.mark.asyncio
async def test_force_refresh_chama_materializar_e_propaga_historico(
    calcular_real: CalcularScoreUseCase,
) -> None:
    exp = datetime.now(UTC) + timedelta(hours=1)
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14="33014556000196",
        payload_bruto={"razao_social": "Nova Razão Oficial"},
        payload_canonico={
            "cnpj": "33014556000196",
            "razao_social": "Nova Razão Oficial",
            "cnae_principal": "4711302",
            "uf": "SP",
            "porte": "micro",
            "regime": "simples_nacional",
            "setor_macro": "comercio",
        },
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    cnpj_svc = AsyncMock()
    cnpj_svc.materializar_consulta = AsyncMock(return_value=mat)
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    uc = RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=calcular_real,
        cnpj_consulta_service=cnpj_svc,
    )
    await uc.execute(_comando_base(force_refresh_cnpj=True))
    cnpj_svc.materializar_consulta.assert_awaited_once()
    kw = repo.salvar_e_materializar_plano_painel.call_args.kwargs
    assert kw["cnpj_consulta_id"] == mat.consulta_id
    hist = kw["historico_campos_empresa_cnpj"]
    assert hist is not None
    assert any(h[0] == "empresa_razao_social" for h in hist)


@pytest.mark.asyncio
async def test_execute_emite_evento_diagnostico_finalizado(
    calcular_real: CalcularScoreUseCase,
) -> None:
    """QDI-H-022 — após persistência, regista ``diagnostico_criado`` e ``diagnostico_finalizado`` (structlog)."""
    repo = AsyncMock()
    repo.salvar_e_materializar_plano_painel = AsyncMock(return_value=_plano_vazio())
    uc = RealizarDiagnostico(repo=repo, calcular_score_use_case=calcular_real)
    cmd = replace(_comando_base(), trace_id="trace-handoff-99")
    with patch("src.application.use_cases.realizar_diagnostico.logger") as log:
        res = await uc.execute(cmd)
    assert res.diagnostico.status.value == "finalizado"
    infos = [c.args[0] for c in log.info.call_args_list if c.args]
    assert infos.count("diagnostico_criado") == 1
    assert infos.count("diagnostico_finalizado") == 1
    assert infos.index("diagnostico_criado") < infos.index("diagnostico_finalizado")
    final_calls = [
        c for c in log.info.call_args_list if c.args and c.args[0] == "diagnostico_finalizado"
    ]
    assert len(final_calls) == 1
    kwa = final_calls[0].kwargs
    assert kwa.get("trace_id") == "trace-handoff-99"
    assert kwa.get("tenant_id") == str(cmd.tenant_id)
    assert kwa.get("diagnostico_id") == str(res.diagnostico.id)
    assert kwa.get("relatorio_pdf") is False
