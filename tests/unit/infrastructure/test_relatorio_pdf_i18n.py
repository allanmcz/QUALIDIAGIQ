"""Testes do pacote i18n do relatório PDF (infra)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.infrastructure.pdf.relatorio_pdf_i18n import (
    formatar_data_geracao_pdf,
    formatar_telefone_exibicao_br,
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
