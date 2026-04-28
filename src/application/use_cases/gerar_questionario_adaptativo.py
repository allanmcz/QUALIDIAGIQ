"""
Caso de Uso: Gerar Questionário Adaptativo.

Camada: Application
Responsabilidade:
    Filtra o banco total de 35 perguntas e devolve apenas as aplicáveis
    ao perfil da Empresa (Regime e Setor Macro).
"""

from src.domain.entities.diagnostico import EmpresaInfo
from src.domain.entities.questionario import Pergunta


class GerarQuestionarioAdaptativoUseCase:
    """Motor de filtro de perguntas."""

    def __init__(self, banco_de_perguntas: list[Pergunta]) -> None:
        """
        Recebe o repositório em memória das 35 perguntas.

        No futuro, esse banco_de_perguntas pode vir de um PerguntaRepository.
        Para o MVP do Sprint 1/2, manteremos as perguntas instanciadas em memória.
        """
        self.banco_de_perguntas = banco_de_perguntas

    def execute(self, empresa: EmpresaInfo) -> list[Pergunta]:
        """
        Filtra as perguntas usando a lógica de negócio do Domain.

        Args:
            empresa: Instância da empresa sendo diagnosticada.

        Returns:
            Lista de perguntas exclusivas e personalizadas para aquele perfil.
        """
        perguntas_filtradas = []

        for pergunta in self.banco_de_perguntas:
            if pergunta.aplicavel_para(empresa):
                perguntas_filtradas.append(pergunta)

        if not perguntas_filtradas:
            raise ValueError(
                "Nenhuma pergunta encontrada para o perfil da empresa. "
                "Verifique a base de conhecimento."
            )

        return perguntas_filtradas
