"""
Use Case principal — orquestra o ciclo completo do diagnóstico.

Camada: Application
Depende de: Domain (entities, value_objects, repositories)
NÃO depende de: Infrastructure, Presentation

Sequência orquestrada:
    1. Captura de lead (CNPJ + e-mail + dados básicos da empresa)
    2. Geração de questionário adaptativo (segmento x regime x porte x UF)
    3. Coleta de respostas
    4. Cálculo de score (motor com pesos transparentes)
    5. Geração de recomendações (regras determinísticas + LLM no Sprint 4)
    6. Geração de PDF (WeasyPrint)
    7. Persistência + envio do relatório
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
    from src.domain.value_objects.score import ScoreComple

from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    Respondente,
)
from src.domain.entities.questionario import Pergunta, Resposta


@dataclass(frozen=True)
class ComandoRealizarDiagnostico:
    """DTO de entrada do use case (Command Pattern)."""

    tenant_id: UUID
    empresa: EmpresaInfo
    respondente: Respondente
    respostas: list[Resposta]
    perguntas_aplicadas: list[Pergunta]


@dataclass(frozen=True)
class ResultadoDiagnostico:
    """DTO de saída — agrega entidade + outputs derivados."""

    diagnostico: Diagnostico
    score: ScoreComple
    relatorio_pdf_url: str | None


class RealizarDiagnostico:
    """
    Use case principal — coordena geração de diagnóstico end-to-end.
    """

    def __init__(
        self,
        repo: DiagnosticoRepository,
        calcular_score_use_case: CalcularScoreUseCase,
    ) -> None:
        self.repo = repo
        self.calcular_score_use_case = calcular_score_use_case

    async def execute(self, comando: ComandoRealizarDiagnostico) -> ResultadoDiagnostico:
        """Executa o pipeline completo do diagnóstico."""
        # 1. Cria a entidade no estado inicial
        diagnostico = Diagnostico(
            tenant_id=comando.tenant_id,
            empresa=comando.empresa,
            respondente=comando.respondente,
        )

        # 2. Calcula o Score usando o motor matemático determinístico
        score_completo = self.calcular_score_use_case.execute(
            perguntas=comando.perguntas_aplicadas, respostas=comando.respostas
        )

        # 3. Finaliza o diagnóstico injetando o score geral consolidado
        diagnostico.finalizar(score_geral=score_completo.score_geral.valor)

        # 4. Persiste no banco de dados (Supabase PostgreSQL via RLS)
        await self.repo.salvar(diagnostico)

        # 5. Retorna o DTO estruturado
        return ResultadoDiagnostico(
            diagnostico=diagnostico,
            score=score_completo,
            relatorio_pdf_url=None,  # PDF será anexado na Sprint 3
        )
