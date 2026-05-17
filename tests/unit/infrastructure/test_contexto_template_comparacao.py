"""Testes do contexto Jinja para PDF de comparação."""

from __future__ import annotations

from src.infrastructure.adapters.pdf_generator_weasyprint import _contexto_template_comparacao


class TestContextoTemplateComparacao:
    def test_destaca_linha_com_respostas_diferentes(self) -> None:
        comparacao = {
            "empresa_razao_social": "ACME",
            "empresa_cnpj": "12345678000199",
            "diagnosticos": [
                {
                    "diagnostico_id": "a",
                    "finalizado_em": "2026-01-01T12:00:00+00:00",
                    "score_geral": 50.0,
                    "numero_interno_grupo": 1,
                },
                {
                    "diagnostico_id": "b",
                    "finalizado_em": "2026-02-01T12:00:00+00:00",
                    "score_geral": 60.0,
                    "numero_interno_grupo": 2,
                },
            ],
            "linhas": [
                {
                    "pergunta_codigo": "Q-FIS-001",
                    "texto_pergunta": "Pergunta?",
                    "valores_por_diagnostico": {
                        "a": {"valor_exibicao": "Sim", "excluida_calculo": False},
                        "b": {"valor_exibicao": "Não", "excluida_calculo": False},
                    },
                }
            ],
        }
        ctx = _contexto_template_comparacao(comparacao, data_geracao="01/01/2026")
        assert len(ctx["colunas"]) == 2
        assert ctx["linhas"][0]["destaque_mudanca"] is True
