"""
Caso de Uso: Calcular Score do Diagnóstico.

Camada: Application
Responsabilidade:
    Recebe um conjunto de respostas puras e as perguntas correspondentes,
    calcula o score de cada dimensão usando médias ponderadas, e consolida
    no Value Object ScoreCompleto.
"""

from datetime import date

from src.domain.entities.questionario import Pergunta, Resposta
from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import (
    Dimensao,
    ScoreCompleto,
    ScoreNumerico,
    exigir_mapa_pesos_macro_completo,
)


class CalcularScoreUseCase:
    """Motor matemático determinístico de pontuação do QDI."""

    def __init__(self, normativa_repo: NormativaScoreMacroRepository) -> None:
        self._normativa_repo = normativa_repo

    def execute(
        self,
        perguntas: list[Pergunta],
        respostas: list[Resposta],
        *,
        data_referencia_normativa: date | None = None,
    ) -> ScoreCompleto:
        """
        Calcula o ScoreCompleto a partir das respostas dadas.

        Args:
            perguntas: Banco de perguntas aplicáveis que foram feitas ao usuário.
            respostas: As respostas preenchidas pelo usuário.
            data_referencia_normativa: Data para resolver pesos macro versionados;
                default `date.today()` (UTC/local do processo).

        Returns:
            ScoreCompleto: O agrupamento consolidado das dimensões e geral.
        """
        if not respostas:
            raise ValueError("Não é possível calcular score sem respostas.")

        data_ref = data_referencia_normativa or date.today()
        pesos_macro_dimensoes = self._normativa_repo.obter_pesos_macro_validos_na_data(data_ref)
        exigir_mapa_pesos_macro_completo(pesos_macro_dimensoes)

        # Cria lookup de perguntas por ID/código para acesso rápido (usaremos codigo para simplificar match)
        mapa_perguntas = {p.id: p for p in perguntas}

        # Agrupamentos para o cálculo
        pontos_por_dimensao: dict[Dimensao, float] = dict.fromkeys(Dimensao, 0.0)
        peso_por_dimensao: dict[Dimensao, float] = dict.fromkeys(Dimensao, 0.0)

        # 1. Acumula pontos ganhos vs pesos possíveis por dimensão
        for resposta in respostas:
            pergunta = mapa_perguntas.get(resposta.pergunta_id)
            if not pergunta:
                raise ValueError(f"Pergunta com ID {resposta.pergunta_id} não encontrada no banco.")

            pontuacao_normalizada = resposta.calcular_pontuacao(pergunta)
            if pontuacao_normalizada is None:
                # Doc 05_QUESTIONARIO §11.1 — "Não se aplica" excluído da média
                continue

            # Matemática da Média Ponderada Interna da Dimensão
            pontos_por_dimensao[pergunta.dimensao] += pontuacao_normalizada * pergunta.peso
            peso_por_dimensao[pergunta.dimensao] += pergunta.peso

        # 2. Gera os Scores Numéricos de cada Dimensão
        scores_das_dimensoes: dict[Dimensao, ScoreNumerico] = {}
        for dimensao in Dimensao:
            peso_aplicado = peso_por_dimensao[dimensao]
            if peso_aplicado > 0:
                # Média Ponderada da dimensão = soma(pontos * peso) / soma(pesos)
                valor_final = pontos_por_dimensao[dimensao] / peso_aplicado
                scores_das_dimensoes[dimensao] = ScoreNumerico(
                    valor=round(valor_final, 2), peso_total_aplicado=peso_aplicado
                )

        if not scores_das_dimensoes:
            raise ValueError("Nenhuma dimensão obteve score.")

        # 3. Gera o Score Geral
        soma_pontos_geral = 0.0
        soma_pesos_macro_aplicados = 0.0

        for dim, score_num in scores_das_dimensoes.items():
            peso_macro = pesos_macro_dimensoes[dim]
            soma_pontos_geral += score_num.valor * peso_macro
            soma_pesos_macro_aplicados += peso_macro

        valor_score_geral = soma_pontos_geral / soma_pesos_macro_aplicados

        score_geral = ScoreNumerico(
            valor=round(valor_score_geral, 2), peso_total_aplicado=soma_pesos_macro_aplicados
        )

        # 4. Retorna Objeto Consolidado
        return ScoreCompleto(
            score_geral=score_geral,
            score_por_dimensao=scores_das_dimensoes,
        )
