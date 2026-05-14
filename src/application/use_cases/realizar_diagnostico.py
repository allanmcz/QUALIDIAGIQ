"""
Use Case principal — orquestra o ciclo completo do diagnóstico.

Camada: Application
Depende de: Domain (entities, value_objects, repositories); **structlog** apenas para eventos de observabilidade (QDI-H-022).
NÃO depende de: Infrastructure, Presentation

Sequência orquestrada:
    1. Captura de contexto (empresa + respondente); **no PDF** a captação de lead exibe só **e-mail** e **telefone**
    2. Geração de questionário adaptativo (segmento x regime x porte x UF)
    3. Coleta de respostas
    4. Cálculo de score (motor com pesos transparentes)
    5. Geração de recomendações (regras determinísticas + LLM no Sprint 4)
    6. Geração de PDF (WeasyPrint)
    7. Persistência + envio do relatório
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.services.cnpj_consulta_mapeamento import mesclar_empresa_com_sugestao_cnpj
from src.application.services.cnpj_consulta_service import CnpjConsultaService
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    Respondente,
)
from src.domain.entities.questionario import Pergunta, Resposta

logger = structlog.get_logger(__name__)

_ANCORA_FIXA_LLM = (
    "Âncoras: EC 132/2023; LC 214/2025; ABNT NBR 17301:2026. "
    "Sugira medidas práticas citando dispositivo aplicável quando possível."
)


def _locale_relatorio_pdf_normalizado(raw: str) -> str:
    """Normaliza idioma do PDF: ``pt-BR`` (default) ou ``en``."""
    v = (raw or "pt-BR").strip().lower().replace("_", "-")
    return "en" if v == "en" else "pt-BR"


if TYPE_CHECKING:
    from src.application.ports.email_service import EmailServicePort
    from src.application.ports.llm_service import LlmServicePort
    from src.application.ports.pdf_generator import PdfGeneratorPort
    from src.application.ports.storage_service import StorageServicePort
    from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
    from src.domain.value_objects.score import ScoreCompleto


@dataclass(frozen=True)
class EntradaRespostaDiagnostico:
    """Par pergunta aplicada + valor bruto — `diagnostico_id` preenchido dentro do use case."""

    pergunta: Pergunta
    valor_bruto: str | int | list[str]


@dataclass(frozen=True)
class ComandoRealizarDiagnostico:
    """DTO de entrada do use case (Command Pattern)."""

    tenant_id: UUID
    empresa: EmpresaInfo
    respondente: Respondente
    entradas_resposta: list[EntradaRespostaDiagnostico]
    plano: str = "gratuito"
    aceite_termos_privacidade: bool = False
    locale_relatorio: str = "pt-BR"
    #: Força nova consulta às fontes públicas ignorando TTL — LC 214/2025 (previsibilidade da evidência).
    force_refresh_cnpj: bool = False
    trace_id: str | None = None


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
        base_normativa_port: BaseNormativaPort | None = None,
        cnpj_consulta_service: CnpjConsultaService | None = None,
    ) -> None:
        self.repo = repo
        self.calcular_score_use_case = calcular_score_use_case
        self.pdf_generator = pdf_generator
        self.storage_service = storage_service
        self.email_service = email_service
        self.llm_service = llm_service
        self.base_normativa_port = base_normativa_port
        self._cnpj_consulta_service = cnpj_consulta_service

    async def execute(self, comando: ComandoRealizarDiagnostico) -> ResultadoDiagnostico:
        """Executa o pipeline completo do diagnóstico."""
        historico_cnpj: list[tuple[str, str | None, str]] = []
        consulta_cnpj_uuid: UUID | None = None
        empresa_efetiva = comando.empresa

        if comando.force_refresh_cnpj and comando.empresa.cnpj:
            if self._cnpj_consulta_service is None:
                raise ValueError(
                    "force_refresh_cnpj exige DATABASE_URL e rede para consulta CNPJ no servidor."
                )
            mat = await self._cnpj_consulta_service.materializar_consulta(
                tenant_id=comando.tenant_id,
                cnpj_14=comando.empresa.cnpj,
                idempotency_key=f"worm-finaliza-{uuid4()}",
                force_refresh=True,
                diagnostico_id=None,
                trace_id=comando.trace_id,
            )
            empresa_efetiva, historico_cnpj = mesclar_empresa_com_sugestao_cnpj(
                comando.empresa,
                mat.payload_canonico,
                cnpj_consulta_14=mat.cnpj_14,
            )
            consulta_cnpj_uuid = mat.consulta_id

        # 1. Cria a entidade no estado inicial
        try:
            plano_enum = PlanoDiagnostico(comando.plano.lower())
        except ValueError:
            plano_enum = PlanoDiagnostico.GRATUITO

        diagnostico = Diagnostico(
            tenant_id=comando.tenant_id,
            empresa=empresa_efetiva,
            respondente=comando.respondente,
            plano=plano_enum,
            locale_relatorio=_locale_relatorio_pdf_normalizado(comando.locale_relatorio),
        )

        if not comando.aceite_termos_privacidade:
            raise ValueError(
                "É obrigatório declarar aceite dos termos de uso e da política de privacidade (LGPD)."
            )
        diagnostico.registrar_aceite_termos_privacidade(datetime.now(UTC))

        perguntas_aplicadas = [e.pergunta for e in comando.entradas_resposta]
        respostas = [
            Resposta(
                diagnostico_id=diagnostico.id,
                pergunta_id=e.pergunta.id,
                pergunta_tipo=e.pergunta.tipo,
                valor_bruto=e.valor_bruto,
            )
            for e in comando.entradas_resposta
        ]

        # 2. Calcula o Score usando o motor matemático determinístico
        score_completo = self.calcular_score_use_case.execute(
            perguntas=perguntas_aplicadas,
            respostas=respostas,
            data_referencia_normativa=datetime.now(UTC).date(),
        )

        # 3. Finaliza e congela evidência em ordem de domínio (hash + snapshot)
        diagnostico.finalizar_e_registrar_evidencia(score_completo)

        # 4. Geração de Recomendações por IA (LLM) liberada temporariamente para todos
        recomendacao_ia = None
        if self.llm_service:
            contexto_empresa = (
                f"Empresa: {diagnostico.empresa.razao_social}\n"
                f"Porte: {diagnostico.empresa.porte.value}\n"
                f"Regime: {diagnostico.empresa.regime.value}\n"
                f"Score Geral: {score_completo.score_geral.valor} "
                f"(Nível: {score_completo.score_geral.nivel.name})\n"
            )

            base_normativa = _ANCORA_FIXA_LLM
            if self.base_normativa_port is not None:
                chunks_ctx = await self.base_normativa_port.buscar_contexto(
                    f"{diagnostico.empresa.regime.value} {diagnostico.empresa.setor_macro.value}",
                    top_k=3,
                    threshold=0.0,
                )
                if chunks_ctx:
                    rag_blob = "\n\n".join(c.texto for c in chunks_ctx)
                    base_normativa = f"{rag_blob}\n\n{_ANCORA_FIXA_LLM}"

            try:
                recomendacao_ia = await self.llm_service.gerar_recomendacao(
                    contexto_empresa=contexto_empresa, base_normativa=base_normativa
                )
            except Exception as exc:
                logger.warning(
                    "recomendacao_llm_excecao_nao_tratada",
                    erro=str(exc),
                    trace_id=comando.trace_id,
                    exc_info=True,
                )
                recomendacao_ia = (
                    "Devido a indisponibilidade temporária do serviço de IA, a recomendação "
                    "personalizada não pôde ser gerada no momento."
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

        # 6. Persiste no banco + materializa plano/matriz/cronograma (mesma operação atómica quando Postgres)
        plano_serializado = await self.repo.salvar_e_materializar_plano_painel(
            diagnostico,
            score_completo,
            historico_campos_empresa_cnpj=historico_cnpj or None,
            cnpj_consulta_id=consulta_cnpj_uuid,
        )

        logger.info(
            "diagnostico_criado",
            tenant_id=str(comando.tenant_id),
            diagnostico_id=str(diagnostico.id),
            status=diagnostico.status.value,
            plano=diagnostico.plano.value,
            trace_id=comando.trace_id,
        )
        logger.info(
            "diagnostico_finalizado",
            tenant_id=str(comando.tenant_id),
            diagnostico_id=str(diagnostico.id),
            status=diagnostico.status.value,
            plano=diagnostico.plano.value,
            relatorio_pdf=bool(pdf_url),
            trace_id=comando.trace_id,
        )

        # 7. Envio de E-mail
        if self.email_service and pdf_url:
            await self.email_service.enviar_email_com_relatorio(
                destinatario_email=diagnostico.respondente.email,
                destinatario_nome=diagnostico.respondente.nome or "Gestor",
                pdf_url=pdf_url,
            )

        # 8. Retorna o DTO estruturado (checklist/matriz/cronograma alinhados ao snapshot materializado)
        return ResultadoDiagnostico(
            diagnostico=diagnostico,
            score=score_completo,
            relatorio_pdf_url=pdf_url,
            recomendacao_ia=recomendacao_ia,
            checklist=list(plano_serializado.checklist),
            matriz_impacto=list(plano_serializado.matriz_impacto),
            cronograma=list(plano_serializado.cronograma),
        )
