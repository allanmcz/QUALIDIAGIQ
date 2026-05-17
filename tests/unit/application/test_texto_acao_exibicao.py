"""Testes de limpeza do sufixo M07 nas descrições de ações."""

from __future__ import annotations

from src.application.services.texto_acao_exibicao import (
    limpar_sufixo_lacuna_score_acao,
    sanitizar_descricoes_checklist_serializado,
)


def test_limpar_sufixo_lacuna_score_acao() -> None:
    bruto = (
        "Parametrizar plano de contas auxiliares — lacuna «Contábil» (score 17.9/100)."
    )
    assert limpar_sufixo_lacuna_score_acao(bruto) == "Parametrizar plano de contas auxiliares"
    assert (
        limpar_sufixo_lacuna_score_acao("Ação sem sufixo.")
        == "Ação sem sufixo."
    )


def test_sanitizar_descricoes_checklist_serializado() -> None:
    checklist = [
        {
            "nome": "Frente",
            "acoes": [
                {
                    "descricao": "Texto — lacuna «Fiscal» (score 28.0/100).",
                    "responsavel": "Fiscal",
                }
            ],
        }
    ]
    out = sanitizar_descricoes_checklist_serializado(checklist)
    assert out[0]["acoes"][0]["descricao"] == "Texto"
