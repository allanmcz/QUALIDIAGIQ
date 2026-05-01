"""Golden parcial M04 — estrutura textual do HTML do relatório (sem binário PDF)."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


def _score_minimo() -> ScoreCompleto:
    sg = ScoreNumerico(valor=72.0, peso_total_aplicado=7.0)
    dims = {
        Dimensao.FISCAL: ScoreNumerico(valor=60.0, peso_total_aplicado=1.0),
        Dimensao.TECNOLOGICA: ScoreNumerico(valor=55.0, peso_total_aplicado=1.0),
    }
    return ScoreCompleto(score_geral=sg, score_por_dimensao=dims)


def _diag_minimo() -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Empresa Template LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=uuid4(),
        empresa=emp,
        respondente=Respondente(email="tpl@teste.com", nome="Fulano"),
    )
    d.finalizar(72.0)
    d.registrar_score_completo_para_evidencia(_score_minimo())
    return d


def test_template_relatorio_contem_secoes_m04_e_normativo() -> None:
    root = Path(__file__).resolve().parents[3]
    templates_dir = root / "src" / "infrastructure" / "templates"
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)
    template = env.get_template("relatorio_diagnostico.html")

    from src.application.services.consultoria_service import ConsultoriaService

    diagnostico = _diag_minimo()
    score = _score_minimo()
    nivel_mapping = {
        "CRITICO": "Crítico",
        "INICIAL": "Inicial",
        "INTERMEDIARIO": "Intermediário",
        "AVANCADO": "Avançado",
        "EXEMPLAR": "Exemplar",
    }
    nivel_geral = nivel_mapping.get(score.score_geral.nivel.name, "N/A")

    checklist = ConsultoriaService.gerar_checklist(diagnostico)
    matriz = ConsultoriaService.gerar_matriz_impacto(diagnostico)
    cronograma = ConsultoriaService.gerar_cronograma_cinco_fases()
    piores = sorted(score.score_por_dimensao.items(), key=lambda kv: kv[1].valor)[:3]
    piores_template = [{"codigo": dim.value, "valor": sn.valor} for dim, sn in piores]

    html = template.render(
        diagnostico=diagnostico,
        score_geral=score.score_geral,
        nivel_geral=nivel_geral,
        dimensoes=score.score_por_dimensao,
        data_geracao="01/01/2026 12:00:00",
        recomendacao_ia=None,
        checklist=checklist,
        matriz_impacto=matriz,
        cronograma=cronograma,
        piores_dimensoes=piores_template,
    )

    assert "M04_SECAO: capa_identificacao" in html
    assert "M04_SECAO: sintese_executiva" in html
    assert "Síntese executiva" in html
    assert "Cronograma em cinco horizontes" in html
    assert "Base legal (referência)" in html
    assert "Matriz de impacto por departamento" in html
