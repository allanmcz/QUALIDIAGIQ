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
    from src.application.ports.email_service import EmailServicePort
    from src.application.ports.pdf_generator import PdfGeneratorPort
    from src.application.ports.storage_service import StorageServicePort
    from src.domain.value_objects.score import ScoreCompleto

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
    score: ScoreCompleto
    relatorio_pdf_url: str | None


class RealizarDiagnostico:
    """
    Use case principal — coordena geração de diagnóstico end-to-end.
    """

    def __init__(
        self,
        repo: DiagnosticoRepository,
        calcular_score_use_case: CalcularScoreUseCase,
        pdf_generator: PdfGeneratorPort | None = None,
        storage_service: StorageServicePort | None = None,
        email_service: EmailServicePort | None = None,
    ) -> None:
        self.repo = repo
        self.calcular_score_use_case = calcular_score_use_case
        self.pdf_generator = pdf_generator
        self.storage_service = storage_service
        self.email_service = email_service

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

        # 4. Geração de PDF e Upload (Se configurado)
        pdf_url = None
        if self.pdf_generator and self.storage_service:
            # Geração (síncrona por design do WeasyPrint na CPU, mas chamamos via adapter)
            pdf_bytes = await self.pdf_generator.gerar_pdf_diagnostico(diagnostico, score_completo)
            
            # Upload para Storage
            pdf_url = await self.storage_service.upload_pdf(
                tenant_id=comando.tenant_id,
                diagnostico_id=diagnostico.id,
                file_bytes=pdf_bytes
            )
            diagnostico.relatorio_pdf_url = pdf_url

        # 5. Persiste no banco de dados (Supabase PostgreSQL via RLS)
        await self.repo.salvar(diagnostico)
        
        # 6. Envio de E-mail
        if self.email_service and pdf_url:
            await self.email_service.enviar_email_com_relatorio(
                destinatario_email=diagnostico.respondente.email,
                destinatario_nome=diagnostico.respondente.nome or "Gestor",
                pdf_url=pdf_url
            )

        # 7. Retorna o DTO estruturado
        return ResultadoDiagnostico(
            diagnostico=diagnostico,
            score=score_completo,
            relatorio_pdf_url=pdf_url,
        )
