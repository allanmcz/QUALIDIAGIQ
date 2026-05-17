"""Testes de montagem de contexto para explicação LLM do score."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.services.explicacao_score_contexto import (
    montar_campos_extras_explicacao_score,
    snapshot_explicacao_score_llm_de_resposta,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.ports.llm_gateway import LlmGatewayResponse
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


class TestMontarCamposExtrasExplicacaoScore:
    """Contexto rico enviado ao gateway."""

    def test_inclui_score_por_dimensao_quando_snapshot_existe(self) -> None:
        d = Diagnostico(
            tenant_id=uuid4(),
            empresa=EmpresaInfo(
                cnpj="12345678000195",
                razao_social="ACME",
                porte=PorteEmpresa.MICRO,
                regime=RegimeTributario.SIMPLES_NACIONAL,
                cnae_principal="1234567",
                uf="SP",
                setor_macro=SetorMacro.COMERCIO,
            ),
            respondente=Respondente(email="a@b.com"),
        )
        d.score_completo_snapshot = ScoreCompleto(
            score_geral=ScoreNumerico(valor=60.0, peso_total_aplicado=1.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=40.0, peso_total_aplicado=1.5),
            },
        )
        d.score_geral = 60.0
        extras = montar_campos_extras_explicacao_score(d)
        assert extras["score_por_dimensao"] == {"fiscal": 40.0}
        assert extras["pesos_por_dimensao"] == {"fiscal": 1.5}
        assert extras["empresa_uf"] == "SP"
        assert extras["empresa_razao_social"] == "ACME"
        assert extras["nivel_maturidade"] == "intermediario"
        assert extras["dimensao_mais_critica"] == "Fiscal"
        assert extras["score_dimensao_mais_critica"] == 40.0

    def test_inclui_faixa_faturamento_quando_informada(self) -> None:
        d = Diagnostico(
            tenant_id=uuid4(),
            empresa=EmpresaInfo(
                cnpj="12345678000195",
                razao_social="ACME",
                porte=PorteEmpresa.MICRO,
                regime=RegimeTributario.SIMPLES_NACIONAL,
                cnae_principal="1234567",
                uf="SP",
                setor_macro=SetorMacro.COMERCIO,
                faixa_faturamento=FaixaFaturamentoDeclarada.ATE_360_MIL,
            ),
            respondente=Respondente(email="a@b.com"),
        )
        extras = montar_campos_extras_explicacao_score(d)
        assert extras["empresa_faixa_faturamento"] == "ate_360_mil"


class TestSnapshotExplicacaoScoreLlm:
    """Serialização para JSONB."""

    def test_snapshot_contem_metadados(self) -> None:
        parecer = (
            "Parecer: score moderado na transição. Priorize fiscal e ERP. "
            "EC 132/2023; LC 214/2025; ABNT NBR 17301:2026."
        )
        out = LlmGatewayResponse(
            text=parecer,
            provider="fake",
            model="m",
            policy_version="v1",
            latency_ms=12,
        )
        snap = snapshot_explicacao_score_llm_de_resposta(
            out, trace_id="tr-1", gerado_em_iso="2026-05-15T10:00:00+00:00"
        )
        assert snap["text"] == parecer
        assert snap["blocked_by_guardrail"] is False
        assert snap["trace_id"] == "tr-1"
        assert snap["gerado_em"] == "2026-05-15T10:00:00+00:00"

    def test_snapshot_marca_bloqueio_quando_fallback_adapter(self) -> None:
        out = LlmGatewayResponse(
            text=(
                "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
                "personalizada não pôde ser gerada no momento."
            ),
            provider="langgraph_ollama",
            model="llama3",
            policy_version="v1",
        )
        snap = snapshot_explicacao_score_llm_de_resposta(
            out, trace_id="tr-2", gerado_em_iso="2026-05-15T10:00:00+00:00"
        )
        assert snap["blocked_by_guardrail"] is True
        assert snap["guardrail_reason"] == "parecer_nao_substantivo"

    def test_rejeita_tipo_invalido(self) -> None:
        with pytest.raises(TypeError):
            snapshot_explicacao_score_llm_de_resposta("x", trace_id="t", gerado_em_iso="z")  # type: ignore[arg-type]
