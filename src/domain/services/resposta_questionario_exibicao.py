"""
Formatação legível de respostas do questionário (PT-BR) para PDF e painel.

Camada: Domain
"""

from __future__ import annotations

import json
from typing import Any

from src.domain.entities.questionario import AlternativaTernaria, Pergunta, TipoPergunta

_ROTULOS_TERNARIA: dict[str, str] = {
    AlternativaTernaria.SIM.value: "Sim",
    AlternativaTernaria.PARCIALMENTE.value: "Parcialmente",
    AlternativaTernaria.NAO.value: "Não",
    "nao_se_aplica": "Não se aplica ao meu negócio",
    "nao_comercializo": "Não comercializo",
    "nao_se_aplica_ao_meu_negocio": "Não se aplica ao meu negócio",
}


def formatar_valor_exibicao_resposta(pergunta: Pergunta, valor_bruto: Any) -> str:
    """Converte valor bruto da API/wizard em texto para relatório e comparação entre ciclos."""
    tipo = pergunta.tipo

    if tipo == TipoPergunta.TERNARIA:
        chave = str(valor_bruto).lower().strip()
        return _ROTULOS_TERNARIA.get(chave, str(valor_bruto))

    if tipo == TipoPergunta.BINARIA:
        v = str(valor_bruto).lower().strip()
        if v in ("sim", "true", "1"):
            return "Sim"
        if v in ("nao", "não", "false", "0"):
            return "Não"
        return str(valor_bruto)

    if tipo == TipoPergunta.ESCALA_1_5:
        try:
            n = int(valor_bruto)
        except (TypeError, ValueError):
            return str(valor_bruto)
        if pergunta.rotulos_escala and 1 <= n <= len(pergunta.rotulos_escala):
            return f"{n} — {pergunta.rotulos_escala[n - 1]}"
        return str(n)

    if tipo in (TipoPergunta.MULTIPLA_ESCOLHA, TipoPergunta.CHECKLIST):
        itens = _lista_valores(valor_bruto)
        if not itens:
            return "—"
        if pergunta.opcoes:
            rotulos = []
            for item in itens:
                try:
                    idx = int(item)
                    if 0 <= idx < len(pergunta.opcoes):
                        rotulos.append(pergunta.opcoes[idx])
                        continue
                except ValueError:
                    pass
                rotulos.append(item)
            return "; ".join(rotulos)
        return "; ".join(itens)

    if tipo == TipoPergunta.NUMERICA:
        return str(valor_bruto)

    return str(valor_bruto)


def _lista_valores(valor_bruto: Any) -> list[str]:
    if isinstance(valor_bruto, list):
        return [str(x).strip() for x in valor_bruto if str(x).strip()]
    if isinstance(valor_bruto, str):
        try:
            parsed = json.loads(valor_bruto)
        except json.JSONDecodeError:
            return [p.strip() for p in valor_bruto.split(",") if p.strip()]
        if isinstance(parsed, list):
            return [str(x).strip() for x in parsed if str(x).strip()]
    return [str(valor_bruto).strip()] if str(valor_bruto).strip() else []
