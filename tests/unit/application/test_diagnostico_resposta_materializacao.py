"""Testes da materialização de linhas de resposta para persistência."""

from __future__ import annotations

from uuid import uuid4

from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.application.services.diagnostico_resposta_materializacao import derivar_respostas_e_linhas
from src.domain.entities.questionario import Pergunta, TipoPergunta
from src.domain.value_objects.score import Dimensao


def test_deriva_linhas_com_ordem_e_codigo() -> None:
    did = uuid4()
    p1 = Pergunta(
        codigo="Q-FIS-001",
        dimensao=Dimensao.FISCAL,
        texto="Primeira",
        peso=2.0,
        tipo=TipoPergunta.TERNARIA,
        base_legal="LC 214/2025 art. 1º",
    )
    p2 = Pergunta(
        codigo="Q-TEC-002",
        dimensao=Dimensao.TECNOLOGICA,
        texto="Segunda",
        peso=1.0,
        tipo=TipoPergunta.TERNARIA,
    )
    entradas = [
        EntradaRespostaDiagnostico(pergunta=p1, valor_bruto="sim"),
        EntradaRespostaDiagnostico(pergunta=p2, valor_bruto="nao_se_aplica"),
    ]
    respostas, linhas = derivar_respostas_e_linhas(did, entradas)
    assert len(respostas) == 2
    assert len(linhas) == 2
    assert linhas[0].ordem_exibicao == 0
    assert linhas[0].pergunta_codigo == "Q-FIS-001"
    assert linhas[0].valor_exibicao == "Sim"
    assert linhas[0].excluida_calculo is False
    assert linhas[1].ordem_exibicao == 1
    assert linhas[1].excluida_calculo is True
    assert linhas[1].pontuacao_item is None
