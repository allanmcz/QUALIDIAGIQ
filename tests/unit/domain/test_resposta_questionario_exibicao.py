"""Testes de formatação PT-BR de respostas do questionário."""

from __future__ import annotations

import pytest

from src.domain.entities.questionario import Pergunta, TipoPergunta
from src.domain.services.resposta_questionario_exibicao import formatar_valor_exibicao_resposta
from src.domain.value_objects.score import Dimensao


def _pergunta(tipo: TipoPergunta, **kwargs: object) -> Pergunta:
    return Pergunta(
        codigo="Q-TEST-001",
        dimensao=Dimensao.FISCAL,
        texto="Pergunta teste",
        peso=1.0,
        tipo=tipo,
        **kwargs,  # type: ignore[arg-type]
    )


class TestFormatarValorExibicaoResposta:
    def test_ternaria_sim(self) -> None:
        p = _pergunta(TipoPergunta.TERNARIA)
        assert formatar_valor_exibicao_resposta(p, "sim") == "Sim"

    def test_ternaria_nao_se_aplica(self) -> None:
        p = _pergunta(TipoPergunta.TERNARIA)
        assert formatar_valor_exibicao_resposta(p, "nao_se_aplica") == "Não se aplica ao meu negócio"

    def test_escala_com_rotulo(self) -> None:
        p = _pergunta(
            TipoPergunta.ESCALA_1_5,
            rotulos_escala=("Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"),
        )
        assert formatar_valor_exibicao_resposta(p, 3) == "3 — Médio"

    @pytest.mark.parametrize("valor,esperado", [("sim", "Sim"), ("nao", "Não")])
    def test_binaria(self, valor: str, esperado: str) -> None:
        p = _pergunta(TipoPergunta.BINARIA)
        assert formatar_valor_exibicao_resposta(p, valor) == esperado
