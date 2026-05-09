"""Testes do pacote i18n do relatório PDF (infra)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.infrastructure.pdf.relatorio_pdf_i18n import (
    formatar_data_geracao_pdf,
    formatar_telefone_exibicao_br,
    nivel_score_labels,
    obter_textos_pdf,
)


@pytest.mark.parametrize(
    "digitos,esperado",
    [
        ("11999998888", "(11) 99999-8888"),
        ("1133334444", "(11) 3333-4444"),
        ("", ""),
        (None, ""),
    ],
)
def test_formatar_telefone_exibicao_br(digitos: str | None, esperado: str) -> None:
    assert formatar_telefone_exibicao_br(digitos) == esperado


def test_obter_textos_pdf_en_tem_partial_notice() -> None:
    en = obter_textos_pdf("en")
    pt = obter_textos_pdf("pt-BR")
    assert en["lead_section_title"] != pt["lead_section_title"]
    assert "Portuguese" in en["partial_locale_notice"]


def test_formatar_data_geracao_en_usa_utc() -> None:
    agora = datetime(2026, 5, 2, 15, 30, 0, tzinfo=UTC)
    assert "2026-05-02" in formatar_data_geracao_pdf("en", agora)
    assert "UTC" in formatar_data_geracao_pdf("en", agora)


def test_formatar_telefone_exibicao_br_fallback_quando_tamanho_invalido() -> None:
    """Quando não há máscara conhecida, retorna os dígitos originais."""
    assert formatar_telefone_exibicao_br("5511999998888") == "5511999998888"


def test_obter_textos_pdf_default_pt_br_quando_locale_desconhecida() -> None:
    txt = obter_textos_pdf("es-AR")
    assert txt["h1_report_title"] == "Relatório de Diagnóstico Tributário"


def test_nivel_score_labels_en_e_pt_br() -> None:
    labels_en = nivel_score_labels("en")
    labels_pt = nivel_score_labels("pt-BR")
    assert labels_en["CRITICO"] == "Critical"
    assert labels_pt["CRITICO"] == "Crítico"


def test_formatar_data_geracao_en_com_data_naive_forca_utc() -> None:
    naive = datetime(2026, 5, 2, 15, 30, 0)
    saida = formatar_data_geracao_pdf("en", naive)
    assert saida.endswith("UTC")


def test_formatar_data_geracao_fallback_quando_agora_invalido() -> None:
    saida = formatar_data_geracao_pdf("pt-BR", agora="invalido")  # type: ignore[arg-type]
    assert "/" in saida and ":" in saida
