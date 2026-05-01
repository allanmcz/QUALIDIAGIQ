"""Testes do carregador JSON do catálogo de perguntas."""

from __future__ import annotations

import json
from uuid import UUID

import pytest

from src.domain.entities.questionario import TipoPergunta
from src.domain.value_objects.score import Dimensao
from src.infrastructure.questionario.json_banco_loader import (
    carregar_banco_mvp,
    carregar_perguntas_de_arquivo,
)


def test_carregar_banco_mvp_catalogo_doc_ids_estaveis() -> None:
    lista = carregar_banco_mvp()
    assert len(lista) == 37
    assert lista[0].id == UUID("df52b20e-dab8-5ce5-a89d-4fb235016cbe")
    assert lista[0].codigo == "Q-EST-001"
    assert lista[0].dimensao == Dimensao.ESTRATEGICA
    assert lista[0].tipo == TipoPergunta.TERNARIA
    assert lista[0].base_legal is not None
    assert "EC 132" in lista[0].base_legal or "LC 214" in lista[0].base_legal


def test_carregar_perguntas_condicional(tmp_path) -> None:
    p = tmp_path / "p.json"
    p.write_text(
        json.dumps(
            {
                "versao_catalogo": "t",
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Teste?",
                        "peso": 1.0,
                        "tipo": "escala_1_5",
                        "base_legal": None,
                        "condicao": {
                            "regimes_permitidos": ["lucro_real"],
                            "setores_permitidos": ["industria"],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    lista = carregar_perguntas_de_arquivo(p)
    assert len(lista) == 1
    c = lista[0].condicao
    assert c is not None
    assert c.regimes_permitidos is not None
    assert c.setores_permitidos is not None


def test_carregar_lista_vazia_erro(tmp_path) -> None:
    p = tmp_path / "empty.json"
    p.write_text(
        json.dumps({"versao_catalogo": "x", "perguntas": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="vazia"):
        carregar_perguntas_de_arquivo(p)
