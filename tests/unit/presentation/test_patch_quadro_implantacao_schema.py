"""Validação HTTP do PATCH quadro de implantação (chaves f{i}_a{j})."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas import PatchQuadroImplantacaoRequest


class TestPatchQuadroImplantacaoRequest:
    def test_aceita_vazio(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate({"quadro_implantacao_anotacoes": {}})
        assert m.quadro_implantacao_anotacoes == {}

    def test_aceita_item_valido(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {"comentario": "Nota", "prazo_meta": "2026-08-01"},
                }
            }
        )
        assert m.quadro_implantacao_anotacoes["f0_a0"].comentario == "Nota"

    def test_rejeita_chave_invalida(self) -> None:
        with pytest.raises(ValidationError, match="Chave"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "0-0": {"comentario": "", "prazo_meta": ""},
                    }
                }
            )

    def test_rejeita_prazo_meta_invalido(self) -> None:
        with pytest.raises(ValidationError, match="prazo_meta"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f1_a2": {"comentario": "", "prazo_meta": "01/08/2026"},
                    }
                }
            )

    def test_rejeita_mais_de_200_chaves(self) -> None:
        grande = {f"f{i}_a0": {"comentario": "", "prazo_meta": ""} for i in range(201)}
        with pytest.raises(ValidationError, match="200"):
            PatchQuadroImplantacaoRequest.model_validate({"quadro_implantacao_anotacoes": grande})
