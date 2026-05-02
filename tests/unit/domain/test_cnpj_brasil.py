"""Testes do validador de CNPJ (DV) — domínio."""

from __future__ import annotations

import pytest

from src.domain.value_objects.cnpj_brasil import (
    cnpj_com_digitos_verificadores_validos,
    exigir_cnpj_vazio_ou_com_dv_ok,
    normalizar_cnpj_apenas_digitos,
)


class TestCnpjBrasil:
    """Casos conhecidos de DV e normalização."""

    @pytest.mark.parametrize(
        "valido",
        [
            "11222333000181",
            "12345678000195",
            "00000000000191",
        ],
    )
    def test_cnpj_valido(self, valido: str) -> None:
        assert cnpj_com_digitos_verificadores_validos(valido)

    @pytest.mark.parametrize(
        "invalido",
        [
            "11222333000180",
            "12345678000194",
            "11111111111111",
            "123",
            "",
        ],
    )
    def test_cnpj_invalido(self, invalido: str) -> None:
        assert not cnpj_com_digitos_verificadores_validos(invalido)

    def test_normalizar_remove_mascara(self) -> None:
        assert normalizar_cnpj_apenas_digitos("11.222.333/0001-81") == "11222333000181"

    def test_exigir_vazio_ok(self) -> None:
        exigir_cnpj_vazio_ou_com_dv_ok("")

    def test_exigir_dv_errado_levanta(self) -> None:
        with pytest.raises(ValueError, match="verificadores"):
            exigir_cnpj_vazio_ou_com_dv_ok("11222333000180")
