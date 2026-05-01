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
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.ports.email_service import EmailServicePort
    from src.application.ports.llm_service import LlmServicePort
    from src.application.ports.pdf_generator import PdfGeneratorPort
    from src.application.ports.storage_service import StorageServicePort
    from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
    from src.domain.entities.questionario import Pergunta, Resposta
    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
    from src.domain.value_objects.score import ScoreCompleto

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    Respondente,
)


@dataclass(frozen=True)
class ComandoRealizarDiagnostico:
    """DTO de entrada do use case (Command Pattern)."""

    tenant_id: UUID
    empresa: EmpresaInfo
    respondente: Respondente
    respostas: list[Resposta]
    perguntas_aplicadas: list[Pergunta]
    plano: str = "gratuito"


@dataclass(frozen=True)
class ResultadoDiagnostico:
    """DTO de saída — agrega entidade + outputs derivados."""

    diagnostico: Diagnostico
    score: ScoreCompleto
    relatorio_pdf_url: str | None
    recomendacao_ia: str | None = None
    checklist: list[dict[str, Any]] | None = None
    matriz_impacto: list[dict[str, Any]] | None = None
    cronograma: list[dict[str, Any]] | None = None


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
        llm_service: LlmServicePort | None = None,
    ) -> None:
        self.repo = repo
        self.calcular_score_use_case = calcular_score_use_case
        self.pdf_generator = pdf_generator
        self.storage_service = storage_service
        self.email_service = email_service
        self.llm_service = llm_service

    async def execute(self, comando: ComandoRealizarDiagnostico) -> ResultadoDiagnostico:
        """Executa o pipeline completo do diagnóstico."""
        # 1. Cria a entidade no estado inicial
        try:
            plano_enum = PlanoDiagnostico(comando.plano.lower())
        except ValueError:
            plano_enum = PlanoDiagnostico.GRATUITO

        diagnostico = Diagnostico(
            tenant_id=comando.tenant_id,
            empresa=comando.empresa,
            respondente=comando.respondente,
            plano=plano_enum,
        )

        # 2. Calcula o Score usando o motor matemático determinístico
        score_completo = self.calcular_score_use_case.execute(
            perguntas=comando.perguntas_aplicadas, respostas=comando.respostas
        )

        # 3. Finaliza o diagnóstico injetando o score geral consolidado
        diagnostico.finalizar(score_geral=score_completo.score_geral.valor)
        diagnostico.registrar_score_completo_para_evidencia(score_completo)

        # 4. Geração de Recomendações por IA (LLM) liberada temporariamente para todos
        recomendacao_ia = None
        if self.llm_service:
            contexto_empresa = (
                f"Empresa: {diagnostico.empresa.razao_social}\\n"
                f"Porte: {diagnostico.empresa.porte.value}\\n"
                f"Regime: {diagnostico.empresa.regime.value}\\n"
                f"Score Geral: {score_completo.score_geral.valor} (Nível: {score_completo.score_geral.nivel.name})\\n"
            )

            # Carregar o texto base normativo (Decreto CBS) para o RAG
            base_normativa = ""
            import os

            caminho_decreto = os.path.join(
                os.path.dirname(__file__),
                "../../../_DEVELOPER/_NOVIDADE/00_RESUMO_EXECUTIVO_Decreto_12955.txt",
            )
            if os.path.exists(caminho_decreto):
                with open(caminho_decreto, encoding="utf-8") as f:
                    # Limitar o tamanho do contexto para evitar estouro de tokens locais (ex: Llama3 tem 8k contexto)
                    base_normativa = f.read()[:4000]

            recomendacao_ia = await self.llm_service.gerar_recomendacao(
                contexto_empresa=contexto_empresa, base_normativa=base_normativa
            )

        # 5. Geração de PDF e Upload (Se configurado)
        pdf_url = None
        if self.pdf_generator and self.storage_service:
            # Geração (síncrona por design do WeasyPrint na CPU, mas chamamos via adapter)
            # Passamos a recomendação IA para ser incluída no PDF se necessário
            pdf_bytes = await self.pdf_generator.gerar_pdf_diagnostico(
                diagnostico, score_completo, recomendacao_ia
            )

            # Upload para Storage
            pdf_url = await self.storage_service.upload_pdf(
                tenant_id=comando.tenant_id, diagnostico_id=diagnostico.id, file_bytes=pdf_bytes
            )
            diagnostico.relatorio_pdf_url = pdf_url

        # 6. Persiste no banco de dados (Supabase PostgreSQL via RLS)
        await self.repo.salvar(diagnostico)

        # 7. Envio de E-mail
        if self.email_service and pdf_url:
            await self.email_service.enviar_email_com_relatorio(
                destinatario_email=diagnostico.respondente.email,
                destinatario_nome=diagnostico.respondente.nome or "Gestor",
                pdf_url=pdf_url,
            )

        # 8. Geração de Consultoria (Checklist e Matriz) liberada temporariamente para todos
        checklist_data = None
        matriz_data = None

        from dataclasses import asdict

        from src.application.services.consultoria_service import ConsultoriaService

        checklist_entities = ConsultoriaService.gerar_checklist(diagnostico)
        matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
        cronograma_data = ConsultoriaService.gerar_cronograma_cinco_fases()
        checklist_data = [asdict(f) for f in checklist_entities]
        matriz_data = [asdict(m) for m in matriz_entities]

        # 9. Retorna o DTO estruturado
        return ResultadoDiagnostico(
            diagnostico=diagnostico,
            score=score_completo,
            relatorio_pdf_url=pdf_url,
            recomendacao_ia=recomendacao_ia,
            checklist=checklist_data,
            matriz_impacto=matriz_data,
            cronograma=cronograma_data,
        )
