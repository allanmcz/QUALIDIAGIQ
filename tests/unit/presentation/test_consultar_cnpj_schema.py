"""Testes — schemas da consulta CNPJ."""

import pytest

from src.presentation.api.schemas import ConsultarCnpjRequest


def test_consultar_cnpj_normaliza_mascarado() -> None:
    r = ConsultarCnpjRequest(cnpj="33.014.556/0001-96")
    assert r.cnpj == "33014556000196"


def test_consultar_cnpj_invalido() -> None:
    with pytest.raises(ValueError):
        ConsultarCnpjRequest(cnpj="11111111111111")


@pytest.mark.parametrize(
    ("texto", "msg"),
    [
        ("12", "14"),
        ("123456780001991", "14"),
    ],
)
def test_consultar_cnpj_tamanho(texto: str, msg: str) -> None:
    with pytest.raises(ValueError, match=msg):
        ConsultarCnpjRequest.model_validate({"cnpj": texto})


def test_consultar_cnpj_dv_invalido() -> None:
    with pytest.raises(ValueError, match="dígitos verificadores"):
        ConsultarCnpjRequest.model_validate({"cnpj": "33014556000190"})


def test_consultar_cnpj_force_refresh_uuid_opcional_json() -> None:
    sid = "01234567-89ab-cdef-0123-456789abcdef"
    r = ConsultarCnpjRequest.model_validate(
        {"cnpj": "33014556000196", "force_refresh": True, "aplicar_no_diagnostico_id": sid}
    )
    assert r.force_refresh is True
    assert str(r.aplicar_no_diagnostico_id) == sid
