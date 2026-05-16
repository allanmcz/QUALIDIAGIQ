"""Checklist serializado HTTP inclui metadados PDCA / horizonte / criticidade (Sprint 1)."""

from __future__ import annotations

import uuid

from src.application.services.plano_painel_derivacao import derivar_plano_painel_materializado
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


def _score_todas_dimensoes(valor: float = 55.0) -> ScoreCompleto:
    sg = ScoreNumerico(valor=valor, peso_total_aplicado=10.0)
    por_dim = {d: ScoreNumerico(valor=valor, peso_total_aplicado=10.0) for d in Dimensao}
    return ScoreCompleto(score_geral=sg, score_por_dimensao=por_dim)


def _diagnostico_micro_sp() -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="ACME",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    return Diagnostico(
        tenant_id=uuid.uuid4(),
        empresa=emp,
        respondente=Respondente(email="t@teste.com"),
    )


class TestPlanoPainelDerivacaoSerializado:
    def test_checklist_acoes_incluem_pdca_horizonte_criticidade_codigo(self) -> None:
        d = _diagnostico_micro_sp()
        sc = _score_todas_dimensoes()
        out = derivar_plano_painel_materializado(d, sc)
        assert out.serializado_http.checklist
        frente0 = out.serializado_http.checklist[0]
        assert frente0.get("acoes")
        ac0 = frente0["acoes"][0]
        assert ac0.get("fase_pdca") in {"PLAN", "DO", "CHECK", "ACT"}
        assert ac0.get("horizonte_planejado")
        assert ac0.get("criticidade_codigo") in {"CRITICA", "ALTA", "MEDIA", "BAIXA"}
        assert ac0.get("plano_acao_id")
        assert ac0.get("chave_quadro_legado", "").startswith("f")
