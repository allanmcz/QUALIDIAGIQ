"""
Configuração de Injeção de Dependências e Segurança.

Camada: Presentation (FastAPI)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import Depends, HTTPException, Query, status

if TYPE_CHECKING:
    from supabase import Client

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.diagnostico_mutacao_audit_port import DiagnosticoMutacaoAuditPort
from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoPort
from src.application.ports.lead_diagnostico_vinculo_port import (
    LeadDiagnosticoVinculoPort,
    NopLeadDiagnosticoVinculoAdapter,
)
from src.application.ports.lgpd_anonimizacao_executor_port import LgpdAnonimizacaoExecutorPort
from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort
from src.application.ports.lgpd_titular_solicitacao_port import LgpdTitularSolicitacaoPort
from src.application.services.cnpj_consulta_service import CnpjConsultaService, CnpjTtlSegundos
from src.application.use_cases.anexar_relatorio_otimista import AnexarRelatorioOtimista
from src.application.use_cases.atualizar_checklist_m12_autoconf import AtualizarChecklistM12Autoconf
from src.application.use_cases.atualizar_quadro_implantacao import AtualizarQuadroImplantacao
from src.application.use_cases.atualizar_status_solicitacao_titular_lgpd import (
    AtualizarStatusSolicitacaoTitularLgpd,
)
from src.application.use_cases.buscar_cnae_subclasses import BuscarCnaeSubclasses
from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.use_cases.consultar_cnpj import ConsultarCnpjUseCase
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ExecutarAnonimizacaoRespondenteLgpd,
)
from src.application.use_cases.executar_eliminacao_diagnostico_lgpd import (
    ExecutarEliminacaoDiagnosticoLgpd,
)
from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    GerarExportPortabilidadeDiagnostico,
)
from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.application.use_cases.listar_retificacoes_diagnostico import (
    ListarRetificacoesDiagnostico,
)
from src.application.use_cases.listar_solicitacao_titular_lgpd import (
    ListarSolicitacaoTitularLgpd,
)
from src.application.use_cases.plano_painel_subtarefa import (
    AtualizarSubtarefaPlanoDiagnostico,
    CriarSubtarefaPlanoDiagnostico,
)
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.application.use_cases.registrar_retificacao_diagnostico import (
    RegistrarRetificacaoDiagnostico,
)
from src.application.use_cases.registrar_solicitacao_titular_lgpd import (
    RegistrarSolicitacaoTitularLgpd,
)
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    VincularDiagnosticosLeadSelfService,
)
from src.domain.entities.diagnostico import (
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PorteEmpresa,
    RegimeTributario,
    SetorMacro,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.repositories.normativa_score_macro_repository import (
    NormativaScoreMacroRepository,
)
from src.domain.value_objects.cnpj_brasil import cnpj_com_digitos_verificadores_validos
from src.infrastructure.adapters.base_normativa_pgvector import PgvectorBaseNormativaAdapter
from src.infrastructure.adapters.base_normativa_stub import StubBaseNormativaAdapter
from src.infrastructure.adapters.cnpj_provedor_externo_http import CnpjProvedorExternoHttpAdapter
from src.infrastructure.adapters.email_smtp import SmtpEmailAdapter
from src.infrastructure.adapters.llm_anthropic import AnthropicLlmAdapter
from src.infrastructure.adapters.llm_langgraph_ollama import LangGraphOllamaLlmAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.adapters.noop_diagnostico_mutacao_audit_adapter import (
    NoOpDiagnosticoMutacaoAuditAdapter,
)
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.adapters.postgres_diagnostico_mutacao_audit_adapter import (
    PostgresDiagnosticoMutacaoAuditAdapter,
)
from src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter import (
    PostgresDiagnosticoRetificacaoAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter import (
    PostgresLgpdAnonimizacaoExecutorAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter import (
    PostgresLgpdEliminacaoExecutorAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter import (
    PostgresLgpdTitularSolicitacaoAdapter,
)
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter
from src.infrastructure.config.settings import get_settings
from src.infrastructure.diagnosticos.memoria_lead_diagnostico_vinculo import (
    MemoriaLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo import (
    PostgresLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.questionario.banco_cache import get_banco_perguntas_cached
from src.infrastructure.repositories.ci_playwright_diagnostico_repository import (
    CiPlaywrightDiagnosticoRepository,
)
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.postgres_cnae_subclasse_repository import (
    PostgresCnaeSubclasseRepository,
)
from src.infrastructure.repositories.postgres_cnpj_consulta_repository import (
    PostgresCnpjConsultaRepository,
)
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api import deps_auth_supabase as _deps_auth_supabase

# Reexport público (rotas e testes importam desde ``dependencies``).
SELF_SERVICE_DIAGNOSTICO_SCOPE = _deps_auth_supabase.SELF_SERVICE_DIAGNOSTICO_SCOPE
get_current_user_tenant = _deps_auth_supabase.get_current_user_tenant
get_self_service_diagnostico_claims = _deps_auth_supabase.get_self_service_diagnostico_claims
get_supabase_client = _deps_auth_supabase.get_supabase_client
require_perfil_manutencao_plataforma = _deps_auth_supabase.require_perfil_manutencao_plataforma

_repo_ci_playwright_singleton: CiPlaywrightDiagnosticoRepository | None = None


def _singleton_ci_playwright_repo() -> CiPlaywrightDiagnosticoRepository:
    global _repo_ci_playwright_singleton
    if _repo_ci_playwright_singleton is None:
        _repo_ci_playwright_singleton = CiPlaywrightDiagnosticoRepository()
    return _repo_ci_playwright_singleton


_UFS_VALIDAS_QUERY = frozenset(
    {
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    }
)

logger = structlog.get_logger(__name__)


def get_diagnostico_repository() -> DiagnosticoRepository:
    """Postgres quando há DSN; sem DSN, repositório CI em memória ou Supabase (PostgREST)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresDiagnosticoRepository(dsn_sync=dsn)
    if settings.ci_playwright_integrated:
        return _singleton_ci_playwright_repo()
    return SupabaseDiagnosticoRepository(client=get_supabase_client())


def get_diagnostico_mutacao_audit_port() -> DiagnosticoMutacaoAuditPort:
    """Auditoria append-only em Postgres; no-op sem DSN síncrono (Supabase / memória)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresDiagnosticoMutacaoAuditAdapter(dsn_sync=dsn)
    return NoOpDiagnosticoMutacaoAuditAdapter()


def get_lead_diagnostico_vinculo_port() -> LeadDiagnosticoVinculoPort:
    """
    Reatribuição self-service → tenant da conta na plataforma.

    Com ``DATABASE_URL`` (DSN síncrono), UPDATE via Postgres. Sem DSN e com modo CI Playwright,
    altera o dict in-process (legado sem Postgres).
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn:
        return PostgresLeadDiagnosticoVinculoAdapter(dsn_sync=dsn)
    if settings.ci_playwright_integrated:
        return MemoriaLeadDiagnosticoVinculoAdapter(
            repo=_singleton_ci_playwright_repo(),
            tenant_self_service=settings.self_service_tenant_id,
        )
    return NopLeadDiagnosticoVinculoAdapter()


def get_lgpd_titular_solicitacao_port() -> LgpdTitularSolicitacaoPort:
    """Port LGPD: exige DSN síncrono para persistir trilha de solicitações do titular."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fluxo LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdTitularSolicitacaoAdapter(dsn_sync=dsn)


def get_registrar_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> RegistrarSolicitacaoTitularLgpd:
    """POST de solicitação do titular (art. 18)."""
    return RegistrarSolicitacaoTitularLgpd(port=port)


def get_listar_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> ListarSolicitacaoTitularLgpd:
    """GET de solicitações do titular por tenant."""
    return ListarSolicitacaoTitularLgpd(port=port)


def get_atualizar_status_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> AtualizarStatusSolicitacaoTitularLgpd:
    """PATCH de status operacional de solicitação LGPD."""
    return AtualizarStatusSolicitacaoTitularLgpd(port=port)


def get_lgpd_anonimizacao_executor_port() -> LgpdAnonimizacaoExecutorPort:
    """Executor físico da anonimização — exige Postgres (mesmo DSN das solicitações)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Execução de anonimização LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdAnonimizacaoExecutorAdapter(dsn_sync=dsn)


def get_executar_anonimizacao_respondente_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
    executor: Annotated[
        LgpdAnonimizacaoExecutorPort,
        Depends(get_lgpd_anonimizacao_executor_port),
    ],
) -> ExecutarAnonimizacaoRespondenteLgpd:
    """Fluxo técnico pós-deferimento (solicitação tipo anonimizacao)."""
    return ExecutarAnonimizacaoRespondenteLgpd(port_solicitacoes=port, executor=executor)


def get_lgpd_eliminacao_executor_port() -> LgpdEliminacaoExecutorPort:
    """Executor físico da eliminação pré-WORM — exige Postgres (mesmo DSN das solicitações)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Execução de eliminação LGPD indisponível sem DATABASE_URL síncrono.",
        )
    return PostgresLgpdEliminacaoExecutorAdapter(dsn_sync=dsn)


def get_executar_eliminacao_diagnostico_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
    executor: Annotated[
        LgpdEliminacaoExecutorPort,
        Depends(get_lgpd_eliminacao_executor_port),
    ],
) -> ExecutarEliminacaoDiagnosticoLgpd:
    """Fluxo técnico pós-deferimento (solicitação tipo eliminacao)."""
    return ExecutarEliminacaoDiagnosticoLgpd(port_solicitacoes=port, executor=executor)


def get_diagnostico_retificacao_port() -> DiagnosticoRetificacaoPort:
    """Append-only de retificações — mesmo DSN síncrono dos fluxos LGPD."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retificações indisponíveis sem DATABASE_URL síncrono.",
        )
    return PostgresDiagnosticoRetificacaoAdapter(dsn_sync=dsn)


def get_gerar_export_portabilidade_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    lgpd: Annotated[LgpdTitularSolicitacaoPort, Depends(get_lgpd_titular_solicitacao_port)],
) -> GerarExportPortabilidadeDiagnostico:
    """Export JSON (+ PDF com anexo) após solicitação LGPD deferida."""
    from src.infrastructure.exportacao.validador_export_diagnostico_v1 import (
        validar_payload_export_diagnostico_v1,
    )
    from src.infrastructure.pdf.portabilidade_pdf_anexo import (
        gerar_pdf_portabilidade_com_json_embebido,
    )

    return GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=lgpd,
        validar_payload_export_v1=validar_payload_export_diagnostico_v1,
        gerar_pdf_com_anexo_json=lambda jb, did, tid: gerar_pdf_portabilidade_com_json_embebido(
            json_bytes=jb,
            diagnostico_id=did,
            tenant_id=tid,
        ),
    )


def get_registrar_retificacao_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    ret: Annotated[DiagnosticoRetificacaoPort, Depends(get_diagnostico_retificacao_port)],
) -> RegistrarRetificacaoDiagnostico:
    """Regista retificação na cadeia WORM (sem alterar diagnóstico original)."""
    return RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret)


def get_listar_retificacoes_diagnostico_use_case(
    ret: Annotated[DiagnosticoRetificacaoPort, Depends(get_diagnostico_retificacao_port)],
) -> ListarRetificacoesDiagnostico:
    """Lista retificações do diagnóstico (mais recentes primeiro)."""
    return ListarRetificacoesDiagnostico(retificacao=ret)


def get_vincular_diagnosticos_lead_self_service_use_case(
    vinculo: Annotated[LeadDiagnosticoVinculoPort, Depends(get_lead_diagnostico_vinculo_port)],
) -> VincularDiagnosticosLeadSelfService:
    """Vincula diagnósticos gratuitos do pool OTP ao tenant do JWT."""
    return VincularDiagnosticosLeadSelfService(vinculo=vinculo)


def get_anexar_relatorio_otimista_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AnexarRelatorioOtimista:
    """PATCH de relatório com versão otimista."""
    return AnexarRelatorioOtimista(repo=repo, mutacao_audit=mutacao_audit)


def get_atualizar_checklist_m12_autoconf_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AtualizarChecklistM12Autoconf:
    """PATCH M12 (autoconf ABNT) com versão otimista."""
    return AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=mutacao_audit)


def get_atualizar_quadro_implantacao_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AtualizarQuadroImplantacao:
    """PATCH quadro de implantação (comentários e prazos) com versão otimista."""
    return AtualizarQuadroImplantacao(repo=repo, mutacao_audit=mutacao_audit)


def get_criar_subtarefa_plano_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> CriarSubtarefaPlanoDiagnostico:
    """POST subtarefa do plano materializado."""
    return CriarSubtarefaPlanoDiagnostico(repo=repo)


def get_atualizar_subtarefa_plano_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> AtualizarSubtarefaPlanoDiagnostico:
    """PATCH subtarefa do plano materializado."""
    return AtualizarSubtarefaPlanoDiagnostico(repo=repo)


def get_normativa_score_macro_repository() -> NormativaScoreMacroRepository:
    """
    Fonte dos pesos macro (agregação score geral).

    Com `DATABASE_URL`, lê `qdi.normativa_score_macro_dimensao`; senão usa constantes embutidas.
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        return EmbutidasNormativaScoreMacroRepository()
    return PostgresNormativaScoreMacroRepository(dsn=dsn)


def get_calcular_score_use_case(
    normativa_repo: Annotated[
        NormativaScoreMacroRepository,
        Depends(get_normativa_score_macro_repository),
    ],
) -> CalcularScoreUseCase:
    """Injeta o motor matemático de Score com resolução de vigência normativa."""
    return CalcularScoreUseCase(normativa_repo=normativa_repo)


def pesos_macro_dimensao_iso_para_http(
    normativa_repo: Annotated[
        NormativaScoreMacroRepository,
        Depends(get_normativa_score_macro_repository),
    ],
) -> dict[str, float]:
    """Snapshot dos pesos macro na data UTC atual — alinhado ao cálculo do POST /diagnosticos/."""
    from datetime import UTC, datetime

    from src.domain.value_objects.score import exigir_mapa_pesos_macro_completo

    ref = datetime.now(UTC).date()
    bruto = normativa_repo.obter_pesos_macro_validos_na_data(ref)
    exigir_mapa_pesos_macro_completo(bruto)
    return {d.value: float(w) for d, w in bruto.items()}


def get_gerar_questionario_adaptativo_use_case() -> GerarQuestionarioAdaptativoUseCase:
    """Motor adaptativo sobre o catálogo JSON em cache."""
    return GerarQuestionarioAdaptativoUseCase(get_banco_perguntas_cached())


def perfil_empresa_para_questionario(
    razao_social: Annotated[str, Query(min_length=1, max_length=255)],
    porte: Annotated[PorteEmpresa, Query()],
    regime: Annotated[RegimeTributario, Query()],
    cnae_principal: Annotated[str, Query(min_length=7, max_length=7)],
    uf: Annotated[str, Query(min_length=2, max_length=2)],
    setor_macro: Annotated[SetorMacro, Query()],
    faixa_faturamento: Annotated[
        FaixaFaturamentoDeclarada | None,
        Query(
            description=(
                "Opcional — faixa de faturamento bruto anual autodeclarada (slug canónico do catálogo)."
            ),
        ),
    ] = None,
    cnpj: Annotated[
        str,
        Query(
            max_length=14,
            description="CNPJ 14 dígitos ou omitido/vazio se não informado.",
        ),
    ] = "",
) -> EmpresaInfo:
    """
    Monta `EmpresaInfo` a partir de query params (mesmas regras do POST, sem máscara).

    Base: docs/refs/05_QUESTIONARIO_v1.md — perfil para filtro condicional.
    """
    cnpj_clean = (cnpj or "").strip()
    if cnpj_clean != "":
        if not cnpj_clean.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ deve conter apenas dígitos",
            )
        if len(cnpj_clean) != 14:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ deve ter 14 dígitos ou ficar vazio",
            )
        if len(set(cnpj_clean)) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ inválido",
            )
        if not cnpj_com_digitos_verificadores_validos(cnpj_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ inválido: dígitos verificadores não conferem",
            )
    ufu = uf.upper()
    if ufu not in _UFS_VALIDAS_QUERY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"UF inválida: {uf}",
        )
    if not cnae_principal.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNAE principal deve conter 7 dígitos",
        )
    return EmpresaInfo(
        cnpj=cnpj_clean,
        razao_social=razao_social.strip(),
        porte=porte,
        regime=regime,
        cnae_principal=cnae_principal,
        uf=ufu,
        setor_macro=setor_macro,
        faixa_faturamento=faixa_faturamento,
    )


def get_pdf_generator() -> WeasyPrintPdfGenerator:
    """Injeta o gerador de PDF."""
    return WeasyPrintPdfGenerator()


def get_storage_service(
    client: Annotated[Client, Depends(get_supabase_client)],
) -> SupabaseStorageAdapter:
    """Injeta o serviço de storage do Supabase."""
    return SupabaseStorageAdapter(client=client)


def get_email_service() -> SmtpEmailAdapter:
    """Injeta o serviço de envio de e-mails."""
    return SmtpEmailAdapter()


def build_base_normativa_port() -> BaseNormativaPort:
    """
    RAG-light: pgvector + embeddings OpenAI quando ``DATABASE_URL`` e ``OPENAI_API_KEY`` existem.
    Caso contrário stub (guardrail usa regex no pós-processamento LLM).
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    key_oai = settings.openai_api_key.get_secret_value().strip() if settings.openai_api_key else ""
    if dsn and key_oai:
        return PgvectorBaseNormativaAdapter(
            dsn=dsn,
            openai_api_key=key_oai,
            embedding_model=settings.openai_embedding_model.strip(),
        )
    return StubBaseNormativaAdapter()


def get_base_normativa_port_dependency() -> BaseNormativaPort:
    """Depends() para use cases que enriquecem prompt com chunks normativos."""
    return build_base_normativa_port()


def get_llm_service() -> LangGraphOllamaLlmAdapter | OllamaLlmAdapter | AnthropicLlmAdapter:
    """
    Injeta LLM — default **LangGraph + LangChain ChatOllama** (Ollama local).

    ``http_ollama``: REST direta. ``anthropic``: Claude com ``ANTHROPIC_API_KEY``.
    Sem chave Anthropic em modo ``anthropic`` → fallback para LangGraph/Ollama (log).
    Ver **ADR-007** e ADR-003.
    """
    settings = get_settings()
    norm = build_base_normativa_port()
    thr = float(settings.qdi_rag_similarity_threshold)
    url = settings.ollama_base_url.strip()
    model = settings.ollama_model.strip()
    timeout = float(settings.ollama_timeout_seconds)

    if settings.llm_backend == "anthropic":
        ak = (
            settings.anthropic_api_key.get_secret_value().strip()
            if settings.anthropic_api_key
            else ""
        )
        if ak:
            return AnthropicLlmAdapter(
                api_key=ak,
                model=settings.anthropic_model.strip(),
                base_normativa_port=norm,
                rag_similarity_threshold=thr,
            )
        logger.warning(
            "llm_backend_anthropic_sem_api_key",
            fallback="langgraph_ollama",
            llm_backend_solicitado="anthropic",
            evento="llm_plano_fallback_backend",
        )

    if settings.llm_backend == "http_ollama":
        return OllamaLlmAdapter(
            ollama_url=url,
            model=model,
            timeout_seconds=timeout,
            base_normativa_port=norm,
            rag_similarity_threshold=thr,
        )
    return LangGraphOllamaLlmAdapter(
        ollama_url=url,
        model=model,
        timeout_seconds=timeout,
        base_normativa_port=norm,
        rag_similarity_threshold=thr,
    )


def _cnpj_consulta_service_optional() -> CnpjConsultaService | None:
    """Monta serviço de CNPJ quando há Postgres local (mesmo critério do repositório de diagnóstico)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        return None
    repo = PostgresCnpjConsultaRepository(dsn)
    provedor = CnpjProvedorExternoHttpAdapter(settings)
    ttl = CnpjTtlSegundos(
        cadastral=settings.qdi_cnpj_ttl_cadastral_seconds,
        qualificacao=settings.qdi_cnpj_ttl_qualificacao_seconds,
        situacao=settings.qdi_cnpj_ttl_situacao_seconds,
    )
    return CnpjConsultaService(repo=repo, provedor=provedor, ttl_segundos=ttl)


def get_consultar_cnpj_use_case(
    repo_diag: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> ConsultarCnpjUseCase:
    """POST ``/referencia/cnpj/consulta_cnpj`` — exige Postgres para trilha ``cnpj_consultas``."""
    svc = _cnpj_consulta_service_optional()
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Consulta CNPJ indisponível: configure DATABASE_URL na API.",
        )
    settings = get_settings()
    dsn = settings.sync_database_url
    assert dsn is not None
    cnpj_repo = PostgresCnpjConsultaRepository(dsn)
    return ConsultarCnpjUseCase(service=svc, cnpj_repo=cnpj_repo, diagnostico_repo=repo_diag)


def get_buscar_cnae_subclasses_use_case() -> BuscarCnaeSubclasses:
    """
    Lookup CNAE via Postgres (`DATABASE_URL`).

    Rota pública (wizard sem login). RLS nas tabelas `qdi.*` aplica-se a roles Supabase;
    a API usa conexão de serviço com SELECT nas migrações 0013/0014.
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Consulta CNAE indisponível: configure DATABASE_URL no serviço da API.",
        )
    repo = PostgresCnaeSubclasseRepository(dsn=dsn)
    return BuscarCnaeSubclasses(repo=repo)


def get_realizar_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    score_use_case: Annotated[CalcularScoreUseCase, Depends(get_calcular_score_use_case)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(get_pdf_generator)],
    storage_service: Annotated[SupabaseStorageAdapter, Depends(get_storage_service)],
    email_service: Annotated[SmtpEmailAdapter, Depends(get_email_service)],
    llm_service: Annotated[
        LangGraphOllamaLlmAdapter | OllamaLlmAdapter | AnthropicLlmAdapter,
        Depends(get_llm_service),
    ],
    base_normativa_port: Annotated[
        BaseNormativaPort,
        Depends(get_base_normativa_port_dependency),
    ],
) -> RealizarDiagnostico:
    """Orquestrador principal."""
    return RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=score_use_case,
        pdf_generator=pdf_generator,
        storage_service=storage_service,
        email_service=email_service,
        llm_service=llm_service,
        base_normativa_port=base_normativa_port,
        cnpj_consulta_service=_cnpj_consulta_service_optional(),
    )
