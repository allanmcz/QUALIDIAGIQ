"""Testes — schemas da consulta CNPJ."""

import pytest

from src.presentation.api.schemas import ConsultarCnpjRequest


def test_consultar_cnpj_normaliza_mascarado() -> None:
    r = ConsultarCnpjRequest(cnpj="33.014.556/0001-96")
    assert r.cnpj == "33014556000196"


def test_consultar_cnpj_invalido() -> None:
    with pytest.raises(ValueError):
        ConsultarCnpjRequest(cnpj="11111111111111")
