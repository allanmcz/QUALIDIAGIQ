"""Golden parcial M04 — estrutura textual do HTML do relatório (sem binário PDF)."""

from __future__ import annotations

from datetime import UTC, datetime
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
from src.infrastructure.pdf.relatorio_pdf_i18n import (
    formatar_data_geracao_pdf,
    formatar_telefone_exibicao_br,
    nivel_score_labels,
    obter_textos_pdf,
)


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
        respondente=Respondente(email="tpl@teste.com", nome="Fulano", telefone="11988887777"),
        locale_relatorio="pt-BR",
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
    locale_pdf = "pt-BR"
    t = obter_textos_pdf(locale_pdf)
    nivel_mapping = nivel_score_labels(locale_pdf)
    nivel_geral = nivel_mapping.get(score.score_geral.nivel.name, "N/A")
    telefone_lead = formatar_telefone_exibicao_br(diagnostico.respondente.telefone)
    data_geracao = formatar_data_geracao_pdf(locale_pdf, datetime.now(UTC))

    checklist = ConsultoriaService.gerar_checklist(diagnostico, score)
    matriz = ConsultoriaService.gerar_matriz_impacto(diagnostico)
    cronograma = ConsultoriaService.gerar_cronograma_cinco_fases()
    piores = sorted(score.score_por_dimensao.items(), key=lambda kv: kv[1].valor)[:3]
    piores_template = [{"codigo": dim.value, "valor": sn.valor} for dim, sn in piores]

    html = template.render(
        diagnostico=diagnostico,
        t=t,
        html_lang="pt-BR",
        telefone_lead_exibicao=telefone_lead,
        score_geral=score.score_geral,
        nivel_geral=nivel_geral,
        dimensoes=score.score_por_dimensao,
        data_geracao=data_geracao,
        recomendacao_ia=None,
        checklist=checklist,
        matriz_impacto=matriz,
        cronograma=cronograma,
        piores_dimensoes=piores_template,
    )

    assert "assets/QDI-NB1-logo-completo.jpg" in html
    assert "M04_SECAO: capa_identificacao" in html
    assert "M04_SECAO: sintese_executiva" in html
    assert "M04_SECAO: tecnico_detalhamento_dimensoes" in html
    assert "M04_SECAO: tecnico_gaps_recomendacoes" in html
    assert t["exec_summary_title"] in html
    assert t["lead_section_title"] in html
    assert telefone_lead in html
    assert "tpl@teste.com" in html
    assert t["schedule_title"] in html
    assert t["th_legal_ref"] in html
    assert t["matrix_title"] in html
