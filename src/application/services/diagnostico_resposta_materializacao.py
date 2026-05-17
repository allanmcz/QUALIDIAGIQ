"""
Deriva linhas normalizadas de respostas do questionário para persistência.

Camada: Application
"""

from __future__ import annotations

from uuid import UUID

from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.domain.entities.questionario import Resposta
from src.domain.services.resposta_questionario_exibicao import formatar_valor_exibicao_resposta
from src.domain.value_objects.linha_resposta_questionario import LinhaRespostaQuestionario


def derivar_respostas_e_linhas(
    diagnostico_id: UUID,
    entradas: list[EntradaRespostaDiagnostico],
) -> tuple[tuple[Resposta, ...], tuple[LinhaRespostaQuestionario, ...]]:
    """
    Converte entradas do POST em ``Resposta`` (motor de score) e linhas imutáveis (BD).

    A ordem das entradas define ``ordem_exibicao`` — alinhada ao wizard adaptativo.
    """
    respostas: list[Resposta] = []
    linhas: list[LinhaRespostaQuestionario] = []

    for ordem, entrada in enumerate(entradas):
        pergunta = entrada.pergunta
        valor = entrada.valor_bruto
        resp = Resposta(
            diagnostico_id=diagnostico_id,
            pergunta_id=pergunta.id,
            pergunta_tipo=pergunta.tipo,
            valor_bruto=valor,
        )
        try:
            pontuacao = resp.calcular_pontuacao(pergunta)
        except ValueError:
            pontuacao = None
        excluida = pontuacao is None

        linhas.append(
            LinhaRespostaQuestionario(
                ordem_exibicao=ordem,
                pergunta_id=pergunta.id,
                pergunta_codigo=pergunta.codigo,
                dimensao=pergunta.dimensao.value,
                tipo_pergunta=pergunta.tipo.value,
                texto_pergunta=pergunta.texto,
                peso=float(pergunta.peso),
                base_legal=pergunta.base_legal,
                pilar_abnt=pergunta.pilar_abnt,
                valor_bruto=valor,
                valor_exibicao=formatar_valor_exibicao_resposta(pergunta, valor),
                pontuacao_item=pontuacao,
                excluida_calculo=excluida,
            )
        )
        respostas.append(resp)

    return tuple(respostas), tuple(linhas)
