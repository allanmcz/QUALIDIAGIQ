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
        assert m.quadro_implantacao_anotacoes["f0_a0"].comentarios == ["Nota"]

    def test_aceita_varios_comentarios(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {"comentarios": ["A", "B"], "prazo_meta": ""},
                }
            }
        )
        assert m.quadro_implantacao_anotacoes["f0_a0"].comentarios == ["A", "B"]

    def test_comentarios_null_equivale_lista_vazia(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {"comentarios": None, "prazo_meta": ""},
                }
            }
        )
        assert m.quadro_implantacao_anotacoes["f0_a0"].comentarios == []

    def test_aceita_descricao_personalizada_no_teto_4000(self) -> None:
        texto = "d" * 4000
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {
                        "comentarios": [],
                        "prazo_meta": "",
                        "descricao_personalizada": texto,
                    },
                }
            }
        )
        assert len(m.quadro_implantacao_anotacoes["f0_a0"].descricao_personalizada) == 4000

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

    def test_rejeita_prazo_meta_formato_nao_iso(self) -> None:
        with pytest.raises(ValidationError, match="prazo_meta"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f0_a1": {"comentarios": [], "prazo_meta": "20260801"},
                    }
                }
            )

    def test_rejeita_mais_de_200_chaves(self) -> None:
        grande = {f"f{i}_a0": {"comentarios": [], "prazo_meta": ""} for i in range(201)}
        with pytest.raises(ValidationError, match="200"):
            PatchQuadroImplantacaoRequest.model_validate({"quadro_implantacao_anotacoes": grande})

    def test_aceita_descricao_personalizada(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {
                        "comentarios": [],
                        "prazo_meta": "",
                        "descricao_personalizada": "Auditar NCM dos 20 principais SKUs",
                    },
                }
            }
        )
        assert m.quadro_implantacao_anotacoes["f0_a0"].descricao_personalizada.startswith("Auditar")

    def test_rejeita_descricao_personalizada_longa_demais(self) -> None:
        longa = "x" * 4001
        with pytest.raises(ValidationError, match="descricao_personalizada"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f0_a0": {
                            "comentarios": [],
                            "prazo_meta": "",
                            "descricao_personalizada": longa,
                        },
                    }
                }
            )

    def test_merge_comentario_legado_quando_lista_vazia(self) -> None:
        m = PatchQuadroImplantacaoRequest.model_validate(
            {
                "quadro_implantacao_anotacoes": {
                    "f0_a0": {"comentario": "  Nota legada  ", "comentarios": []},
                }
            }
        )
        assert m.quadro_implantacao_anotacoes["f0_a0"].comentarios == ["Nota legada"]

    def test_rejeita_comentarios_nao_lista(self) -> None:
        """``field_validator(..., mode='before')`` com ``TypeError`` (Pydantic não envolve)."""
        with pytest.raises(TypeError, match="lista de strings"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f0_a0": {"comentarios": "não é lista", "prazo_meta": ""},
                    }
                }
            )

    def test_rejeita_mais_de_30_comentarios(self) -> None:
        varios = [f"c{i}" for i in range(31)]
        with pytest.raises(ValidationError, match="30"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f0_a0": {"comentarios": varios, "prazo_meta": ""},
                    }
                }
            )

    def test_rejeita_comentario_item_longo(self) -> None:
        longo = "x" * 2001
        with pytest.raises(ValidationError, match="2000"):
            PatchQuadroImplantacaoRequest.model_validate(
                {
                    "quadro_implantacao_anotacoes": {
                        "f0_a0": {"comentarios": [longo], "prazo_meta": ""},
                    }
                }
            )
