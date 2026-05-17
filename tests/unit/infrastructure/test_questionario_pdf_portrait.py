"""PDF do questionário — orientação retrato e folhas de estilo dedicadas."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def _templates_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "infrastructure" / "templates"


def test_questionario_pdf_css_declara_retrato() -> None:
    css = (_templates_dir() / "questionario_pdf.css").read_text(encoding="utf-8")
    assert "size: A4 portrait" in css
    assert "pdf-questionario" in css


def test_comparacao_questionario_pdf_css_declara_retrato() -> None:
    css = (_templates_dir() / "comparacao_questionario_pdf.css").read_text(encoding="utf-8")
    assert "size: A4 portrait" in css


def test_template_questionario_respostas_usa_classe_retrato() -> None:
    env = Environment(loader=FileSystemLoader(_templates_dir()), autoescape=True)
    html = env.get_template("questionario_respostas.html").render(
        empresa_razao="Empresa Teste",
        empresa_cnpj="12345678000195",
        diagnostico_id="22222222-2222-4222-a222-222222222222",
        finalizado_em="01/01/2026",
        data_geracao="01/01/2026",
        hash_evidencia="",
        respostas=[
            {
                "ordem_exibicao": 0,
                "pergunta_codigo": "Q-001",
                "texto_pergunta": "Pergunta exemplo?",
                "base_legal": "LC 214/2025 art. 1º",
                "valor_exibicao": "Sim",
                "excluida_calculo": False,
                "pontuacao_item": 10.0,
            }
        ],
    )
    assert 'class="pdf-questionario"' in html
    assert "<colgroup>" in html
