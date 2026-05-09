"""Classificação editorial ``origem_motor`` por nome de frente (derivacao painel)."""

from __future__ import annotations

import pytest

from src.application.services.plano_painel_derivacao import _origem_motor_por_nome_frente


@pytest.mark.parametrize(
    ("nome_frente", "esperado"),
    [
        ("lacunas e riscos", "M07"),
        ("Prioridade zero fiscal", "M07"),
        ("Governança e Comitê RTC", "GOVERNANCA"),
        ("Governança inicial", "GOVERNANCA"),
        ("TI / ERP modernização", "TI_ERP"),
        ("Cadastros mestres CBS", "CADASTROS"),
        ("Contratos com fornecedores", "CONTRATOS"),
        ("Compliance ABNT NBR 17301", "ABNT10"),
        ("Fiscal genérico sem keyword editorial", "OUTROS"),
    ],
)
def test_origem_motor_por_nome_frente(nome_frente: str, esperado: str) -> None:
    assert _origem_motor_por_nome_frente(nome_frente) == esperado
