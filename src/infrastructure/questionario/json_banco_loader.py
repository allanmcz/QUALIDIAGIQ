"""
Carrega o banco de perguntas a partir de JSON versionado no repositório.

Camada: Infrastructure
Analogia: equivale a ler um `.INI` ou `.XML` de cadastro no Winthor e hidratar registros em memória,
sem misturar parsing com regra de negócio no domain.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from src.domain.entities.diagnostico import PorteEmpresa, RegimeTributario, SetorMacro
from src.domain.entities.questionario import CondicaoExibicao, Pergunta, TipoPergunta
from src.domain.value_objects.score import Dimensao

_DIR_DATA = Path(__file__).resolve().parent / "data"
_ARQUIVO_PADRAO = _DIR_DATA / "perguntas_mvp.json"


def _parse_condicao(raw: object) -> CondicaoExibicao | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("Campo 'condicao' deve ser objeto ou null.")

    regimes_raw = raw.get("regimes_permitidos")
    setores_raw = raw.get("setores_permitidos")
    setores_excl_raw = raw.get("setores_excluidos")
    portes_raw = raw.get("portes_permitidos")

    regimes: tuple[RegimeTributario, ...] | None = None
    if regimes_raw is not None:
        if not isinstance(regimes_raw, list):
            raise ValueError("regimes_permitidos deve ser lista de strings.")
        regimes = tuple(RegimeTributario(str(x)) for x in regimes_raw)

    setores: tuple[SetorMacro, ...] | None = None
    if setores_raw is not None:
        if not isinstance(setores_raw, list):
            raise ValueError("setores_permitidos deve ser lista de strings.")
        setores = tuple(SetorMacro(str(x)) for x in setores_raw)

    setores_excl: tuple[SetorMacro, ...] | None = None
    if setores_excl_raw is not None:
        if not isinstance(setores_excl_raw, list):
            raise ValueError("setores_excluidos deve ser lista de strings.")
        setores_excl = tuple(SetorMacro(str(x)) for x in setores_excl_raw)

    portes: tuple[PorteEmpresa, ...] | None = None
    if portes_raw is not None:
        if not isinstance(portes_raw, list):
            raise ValueError("portes_permitidos deve ser lista de strings.")
        portes = tuple(PorteEmpresa(str(x)) for x in portes_raw)

    return CondicaoExibicao(
        regimes_permitidos=regimes,
        setores_permitidos=setores,
        setores_excluidos=setores_excl,
        portes_permitidos=portes,
    )


def carregar_perguntas_de_arquivo(caminho: Path) -> list[Pergunta]:
    """Lê JSON e devolve entidades de domínio `Pergunta`."""
    texto = caminho.read_text(encoding="utf-8")
    raiz = json.loads(texto)
    if not isinstance(raiz, dict):
        raise ValueError("Raiz do JSON deve ser um objeto.")
    itens = raiz.get("perguntas")
    if not isinstance(itens, list) or not itens:
        raise ValueError("Lista 'perguntas' ausente ou vazia.")

    resultado: list[Pergunta] = []
    for i, item in enumerate(itens):
        if not isinstance(item, dict):
            raise ValueError(f"perguntas[{i}] deve ser objeto.")

        pid = UUID(str(item["id"]))
        codigo = str(item["codigo"])
        dim = Dimensao(str(item["dimensao"]))
        texto_pergunta = str(item["texto"])
        peso = float(item["peso"])
        tipo = TipoPergunta(str(item["tipo"]))
        base_legal = item.get("base_legal")
        bl_out: str | None = str(base_legal) if base_legal is not None else None
        condicao = _parse_condicao(item.get("condicao"))
        multipla_raw = item.get("multipla_total")
        multipla_total = int(multipla_raw) if multipla_raw is not None else None
        opcoes_raw = item.get("opcoes")
        opcoes: tuple[str, ...] | None = None
        if isinstance(opcoes_raw, list) and opcoes_raw:
            opcoes = tuple(str(x) for x in opcoes_raw)

        resultado.append(
            Pergunta(
                id=pid,
                codigo=codigo,
                dimensao=dim,
                texto=texto_pergunta,
                peso=peso,
                tipo=tipo,
                base_legal=bl_out,
                condicao=condicao,
                multipla_total=multipla_total,
                opcoes=opcoes,
            )
        )
    return resultado


def carregar_banco_mvp() -> list[Pergunta]:
    """Catálogo embutido para o MVP (substituível depois por DB/Lexiq)."""
    return carregar_perguntas_de_arquivo(_ARQUIVO_PADRAO)
