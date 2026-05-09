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
    assert lista[0].pilar_abnt is not None and "17301" in lista[0].pilar_abnt
    assert lista[1].pilar_abnt is not None and "17301" in lista[1].pilar_abnt


def test_pilar_abnt_opcional_no_json(tmp_path) -> None:
    p = tmp_path / "pilares.json"
    p.write_text(
        json.dumps(
            {
                "versao_catalogo": "t",
                "perguntas": [
                    {
                        "id": "bbbbbbbb-bbbb-4bbb-bbbb-bbbbbbbbbbbb",
                        "codigo": "Q-Z",
                        "dimensao": "fiscal",
                        "texto": "Teste sem pilar?",
                        "peso": 2.0,
                        "tipo": "binaria",
                        "base_legal": "LC 214/2025",
                        "condicao": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    lista = carregar_perguntas_de_arquivo(p)
    assert lista[0].pilar_abnt is None


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


def test_escala_1_5_com_rotulos_escala_cinco_itens() -> None:
    lista = carregar_banco_mvp()
    abnt1 = next(p for p in lista if p.codigo == "Q-ABNT-001")
    assert abnt1.tipo == TipoPergunta.ESCALA_1_5
    assert abnt1.rotulos_escala is not None
    assert len(abnt1.rotulos_escala) == 5
    assert "Maduro" in abnt1.rotulos_escala[4]


def test_rotulos_escala_tamanho_invalido_erro(tmp_path) -> None:
    p = tmp_path / "bad_scale.json"
    p.write_text(
        json.dumps(
            {
                "versao_catalogo": "t",
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Escala?",
                        "peso": 1.0,
                        "tipo": "escala_1_5",
                        "base_legal": None,
                        "condicao": None,
                        "rotulos_escala": ["a", "b", "c"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exatamente 5"):
        carregar_perguntas_de_arquivo(p)


def test_rotulos_escala_so_para_escala_erro(tmp_path) -> None:
    p = tmp_path / "bad_bin.json"
    p.write_text(
        json.dumps(
            {
                "versao_catalogo": "t",
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Bin?",
                        "peso": 1.0,
                        "tipo": "binaria",
                        "base_legal": None,
                        "condicao": None,
                        "rotulos_escala": ["1", "2", "3", "4", "5"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="escala_1_5"):
        carregar_perguntas_de_arquivo(p)


def test_carregar_lista_vazia_erro(tmp_path) -> None:
    p = tmp_path / "empty.json"
    p.write_text(
        json.dumps({"versao_catalogo": "x", "perguntas": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="vazia"):
        carregar_perguntas_de_arquivo(p)


def test_carregar_rejeita_raiz_nao_objeto(tmp_path) -> None:
    p = tmp_path / "raiz_lista.json"
    p.write_text(json.dumps([{"perguntas": []}]), encoding="utf-8")
    with pytest.raises(ValueError, match="Raiz do JSON deve ser um objeto"):
        carregar_perguntas_de_arquivo(p)


def test_carregar_rejeita_item_pergunta_nao_objeto(tmp_path) -> None:
    p = tmp_path / "item_invalido.json"
    p.write_text(json.dumps({"perguntas": ["x"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="perguntas\\[0\\] deve ser objeto"):
        carregar_perguntas_de_arquivo(p)


def test_parse_condicao_rejeita_tipos_invalidos(tmp_path) -> None:
    p = tmp_path / "condicao_invalida.json"
    p.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Teste",
                        "peso": 1.0,
                        "tipo": "binaria",
                        "condicao": {"regimes_permitidos": "lucro_real"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="regimes_permitidos deve ser lista"):
        carregar_perguntas_de_arquivo(p)


def test_rotulos_escala_rejeita_string_vazia(tmp_path) -> None:
    p = tmp_path / "rotulos_vazios.json"
    p.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Escala",
                        "peso": 1.0,
                        "tipo": "escala_1_5",
                        "rotulos_escala": ["1", "2", " ", "4", "5"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="não pode conter string vazia"):
        carregar_perguntas_de_arquivo(p)


@pytest.mark.parametrize(
    "condicao,msg",
    [
        ({"setores_permitidos": "industria"}, "setores_permitidos deve ser lista"),
        ({"setores_excluidos": "servicos"}, "setores_excluidos deve ser lista"),
        ({"portes_permitidos": "medio"}, "portes_permitidos deve ser lista"),
    ],
)
def test_parse_condicao_rejeita_listas_obrigatorias(tmp_path, condicao, msg) -> None:
    p = tmp_path / "condicao_lista_obrigatoria.json"
    p.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Teste",
                        "peso": 1.0,
                        "tipo": "binaria",
                        "condicao": condicao,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match=msg):
        carregar_perguntas_de_arquivo(p)


def test_carregar_opcoes_quando_lista_nao_vazia(tmp_path) -> None:
    p = tmp_path / "opcoes_ok.json"
    p.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Teste",
                        "peso": 1.0,
                        "tipo": "multipla_escolha",
                        "multipla_total": 2,
                        "opcoes": ["a", "b"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    lista = carregar_perguntas_de_arquivo(p)
    assert lista[0].opcoes == ("a", "b")


def test_rotulos_escala_rejeita_quando_nao_lista(tmp_path) -> None:
    p = tmp_path / "rotulos_nao_lista.json"
    p.write_text(
        json.dumps(
            {
                "perguntas": [
                    {
                        "id": "aaaaaaaa-bbbb-4ccc-dddd-eeeeeeeeeeee",
                        "codigo": "Q-X",
                        "dimensao": "contabil",
                        "texto": "Escala",
                        "peso": 1.0,
                        "tipo": "escala_1_5",
                        "rotulos_escala": "1,2,3,4,5",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="deve ser lista ou null"):
        carregar_perguntas_de_arquivo(p)
