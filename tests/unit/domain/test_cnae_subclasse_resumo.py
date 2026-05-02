"""Testes do value object CnaeSubclasseResumo (DOMAIN)."""

from __future__ import annotations

import pytest

from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo


class TestCnaeSubclasseResumo:
    """Invariantes do identificador CNAE 7 dígitos."""

    def test_aceita_valido(self) -> None:
        r = CnaeSubclasseResumo(
            subclasse_id="6201501",
            descricao="Desenvolvimento de programas de computador sob encomenda",
        )
        assert r.subclasse_id == "6201501"

    @pytest.mark.parametrize("sid", ["", "123", "123456", "12345678", "abcdefg"])
    def test_rejeita_id_invalido(self, sid: str) -> None:
        with pytest.raises(ValueError, match="7 dígitos"):
            CnaeSubclasseResumo(subclasse_id=sid, descricao="X")

    def test_rejeita_descricao_vazia(self) -> None:
        with pytest.raises(ValueError, match="descricao"):
            CnaeSubclasseResumo(subclasse_id="6201501", descricao="   ")
