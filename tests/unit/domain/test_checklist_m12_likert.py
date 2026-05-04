"""Testes do value object Likert M12 (camada DOMAIN)."""

from __future__ import annotations

import pytest

from src.domain.value_objects.checklist_m12_likert import (
    M12_NUM_ITENS,
    normalizar_checklist_m12_estado_bruto,
    validar_itens_m12_likert,
)


class TestChecklistM12Likert:
    """Invariantes da escala 1-5 e normalização de JSON legado (booleanos)."""

    def test_validar_aceita_dez_itens(self) -> None:
        itens = [1, 2, 3, 4, 5, 3, 3, 3, 2, 1]
        validar_itens_m12_likert(itens)

    def test_validar_rejeita_tamanho(self) -> None:
        with pytest.raises(ValueError, match="exatamente"):
            validar_itens_m12_likert([3] * (M12_NUM_ITENS - 1))

    def test_validar_rejeita_fora_intervalo(self) -> None:
        with pytest.raises(ValueError, match="índice 2"):
            validar_itens_m12_likert([1, 2, 6, 1, 1, 1, 1, 1, 1, 1])

    def test_normalizar_booleanos_para_likert(self) -> None:
        raw = [True, False] * 5
        out = normalizar_checklist_m12_estado_bruto(raw)
        assert out == [5, 1, 5, 1, 5, 1, 5, 1, 5, 1]

    def test_normalizar_inteiros_preserva(self) -> None:
        raw = [3] * M12_NUM_ITENS
        assert normalizar_checklist_m12_estado_bruto(raw) == raw

    def test_normalizar_rejeita_lista_curta(self) -> None:
        assert normalizar_checklist_m12_estado_bruto([1, 2, 3]) is None
