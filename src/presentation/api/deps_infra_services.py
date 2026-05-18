"""
Normativa RAG-light, LLM, score macro, questionário, CNPJ/CNAE, PDF, storage, e-mail e orquestrador.

Camada: Presentation (FastAPI)

Extraído de ``dependencies.py`` (Onda 2 — fatia infra/serviços externos).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Query, Request, status
from supabase import Client  # noqa: TC002 — runtime: geração OpenAPI/Pydantic com Depends

from src.application.ports.base_normativa_port import BaseNormativaPort
from src.application.ports.llm_service import LlmServicePort
from src.application.services.cnpj_consulta_service import CnpjConsultaService, CnpjTtlSegundos
from src.application.use_cases.buscar_cnae_subclasses import BuscarCnaeSubclasses
from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.use_cases.consultar_cnpj import ConsultarCnpjUseCase
from src.application.use_cases.explicar_score_llm_use_case import ExplicarScoreLlmUseCase
from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.domain.entities.diagnostico import (
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PorteEmpresa,
    RegimeTributario,
    SetorMacro,
)
from src.domain.ports.llm_gateway import LlmGateway
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.repositories.normativa_pergunta_peso_repository import (
    NormativaPerguntaPesoRepository,
)
from src.domain.repositories.normativa_score_macro_repository import (
    NormativaScoreMacroRepository,
)
from src.domain.value_objects.cnpj_brasil import cnpj_com_digitos_verificadores_validos
from src.domain.value_objects.score import PesoMacroNormativoVigente
from src.infrastructure.adapters.base_normativa_composite import CompositeBaseNormativaAdapter
from src.infrastructure.adapters.base_normativa_ollama_local import OllamaLocalBaseNormativaAdapter
from src.infrastructure.adapters.base_normativa_pgvector import PgvectorBaseNormativaAdapter
from src.infrastructure.adapters.base_normativa_stub import StubBaseNormativaAdapter
from src.infrastructure.adapters.cnpj_provedor_externo_http import CnpjProvedorExternoHttpAdapter
from src.infrastructure.adapters.email_smtp import SmtpEmailAdapter
from src.infrastructure.adapters.llm_adapter_factory import build_llm_adapter_from_settings
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.gateway_router import LlmGatewayRouter
from src.infrastructure.questionario.banco_cache import get_banco_perguntas_cached
from src.infrastructure.repositories.embutidas_normativa_pergunta_peso_repository import (
    EmbutidasNormativaPerguntaPesoRepository,
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
from src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository import (
    PostgresNormativaPerguntaPesoRepository,
)
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)
from src.presentation.api.deps_auth_supabase import get_supabase_client
from src.presentation.api.deps_repositories_core import (
    get_diagnostico_repository,
    get_empresa_painel_arquivo_port,
)
from src.presentation.api.jwt_llm_tier_context import llm_tier_context_from_authorization

logger = structlog.get_logger(__name__)

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


def get_normativa_pergunta_peso_repository() -> NormativaPerguntaPesoRepository:
    """
    Overlay opcional de pesos por pergunta sobre o catálogo JSON.

    Com ``DATABASE_URL``, lê ``qdi.normativa_pergunta_peso``; senão devolve mapa vazio (só JSON).
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn is None:
        return EmbutidasNormativaPerguntaPesoRepository()
    return PostgresNormativaPerguntaPesoRepository(dsn)


def get_calcular_score_use_case(
    normativa_repo: Annotated[
        NormativaScoreMacroRepository,
        Depends(get_normativa_score_macro_repository),
    ],
) -> CalcularScoreUseCase:
    """Injeta o motor matemático de Score com resolução de vigência normativa."""
    return CalcularScoreUseCase(normativa_repo=normativa_repo)


@dataclass(frozen=True, slots=True)
class PesosMacroPublicacaoHttp:
    """Snapshot público: valores numéricos + metadados de vigência por dimensão (domínio)."""

    valores: dict[str, float]
    metadados_por_dimensao: dict[str, PesoMacroNormativoVigente]


def pesos_macro_publicacao_para_http(
    normativa_repo: Annotated[
        NormativaScoreMacroRepository,
        Depends(get_normativa_score_macro_repository),
    ],
) -> PesosMacroPublicacaoHttp:
    """
    Pesos macro na data UTC corrente — **mesma** resolução que o POST ``/diagnosticos/``.

    Expõe vigência para auditoria (LC 214/2025; ABNT NBR 17301:2026). O router converte para schema HTTP.
    """
    from datetime import UTC, datetime

    from src.domain.value_objects.score import exigir_mapa_pesos_macro_completo

    ref = datetime.now(UTC).date()
    meta = normativa_repo.obter_metadados_macro_validos_na_data(ref)
    bruto = {d: m.peso for d, m in meta.items()}
    exigir_mapa_pesos_macro_completo(bruto)
    valores = {d.value: float(w) for d, w in bruto.items()}
    metadados_iso = {d.value: m for d, m in meta.items()}
    return PesosMacroPublicacaoHttp(valores=valores, metadados_por_dimensao=metadados_iso)


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
    RAG-light (Onda IA 1.1): pgvector, Ollama local, composite ou stub.

    ``auto``: pgvector se ``DATABASE_URL`` + ``OPENAI_API_KEY``; acrescenta Ollama local em dev;
    senão só Ollama local; sem nenhum → stub.
    """
    settings = get_settings()
    dsn = settings.sync_database_url
    key_oai = settings.openai_api_key.get_secret_value().strip() if settings.openai_api_key else ""
    backend = settings.qdi_rag_backend.strip().lower()
    adapters: list[BaseNormativaPort] = []

    def _pgvector() -> PgvectorBaseNormativaAdapter | None:
        if not (dsn and key_oai):
            return None
        return PgvectorBaseNormativaAdapter(
            dsn=dsn,
            openai_api_key=key_oai,
            embedding_model=settings.openai_embedding_model.strip(),
        )

    def _ollama_local() -> OllamaLocalBaseNormativaAdapter:
        cache_path = settings.qdi_rag_codigo_index_path.strip()
        return OllamaLocalBaseNormativaAdapter(
            settings.ollama_base_url,
            embedding_model=settings.ollama_embedding_model,
            incluir_adrs=settings.qdi_rag_incluir_adrs,
            codigo_index_json=cache_path or None,
            timeout_seconds=settings.ollama_timeout_seconds,
        )

    if backend == "pgvector":
        pg = _pgvector()
        return pg if pg is not None else StubBaseNormativaAdapter()
    if backend == "ollama_local":
        return _ollama_local()
    if backend == "composite":
        pg = _pgvector()
        if pg is not None:
            adapters.append(pg)
        adapters.append(_ollama_local())
        return CompositeBaseNormativaAdapter(*adapters)

    # auto
    pg = _pgvector()
    if pg is not None:
        adapters.append(pg)
    adapters.append(_ollama_local())
    if not adapters:
        return StubBaseNormativaAdapter()
    if len(adapters) == 1:
        return adapters[0]
    return CompositeBaseNormativaAdapter(*adapters)


def get_base_normativa_port_dependency() -> BaseNormativaPort:
    """Depends() para use cases que enriquecem prompt com chunks normativos."""
    return build_base_normativa_port()


def get_llm_service(request: Request) -> LlmServicePort:
    """
    Injeta LLM — delega em ``build_llm_adapter_from_settings`` (**ADR-021**).

    Default: **LangGraph + LangChain ChatOllama** (Ollama local). Ver **ADR-007** e ADR-003.
    Tier de observabilidade: JWT assinado (``qdi_llm_tier`` / ``perfil_conta``) + Settings (**2.3.1**).
    """
    settings = get_settings()
    norm = build_base_normativa_port()
    thr = float(settings.qdi_rag_similarity_threshold)
    auth = request.headers.get("Authorization")
    claim_tier, perfil = llm_tier_context_from_authorization(
        auth,
        jwt_secret=settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    return build_llm_adapter_from_settings(
        settings,
        base_normativa_port=norm,
        rag_similarity_threshold=thr,
        tier_jwt_claim=claim_tier,
        perfil_conta_jwt=perfil,
    )


def get_llm_gateway_operacional(request: Request) -> LlmGateway:
    """
    Gateway LLM com router activo para fluxos de produto (**ADR-022**).

    Usa *snapshot* de settings com ``llm_router_enabled=True`` para não depender do default global;
    o kill-switch ``LLM_ROUTER_ENABLED=false`` mantém efeito em ``get_llm_gateway`` (sem override).
    """
    settings = get_settings()
    activos = settings.model_copy(update={"llm_router_enabled": True})
    return LlmGatewayRouter(activos, llm_service=get_llm_service(request))


def get_llm_gateway(request: Request) -> LlmGateway:
    """Gateway convergente respeitando ``LLM_ROUTER_ENABLED`` (testes / kill-switch)."""
    return LlmGatewayRouter(get_settings(), llm_service=get_llm_service(request))


def get_explicar_score_llm_use_case(
    llm_gateway: Annotated[LlmGateway, Depends(get_llm_gateway_operacional)],
) -> ExplicarScoreLlmUseCase:
    """Narrativa sobre score via gateway + RAG Lexiq (Onda IA 1.1)."""
    settings = get_settings()
    pv = settings.llm_router_policy_version.strip() or "2026-05-15-v1"
    return ExplicarScoreLlmUseCase(
        gateway=llm_gateway,
        base_normativa_port=build_base_normativa_port(),
        rag_similarity_threshold=float(settings.qdi_rag_similarity_threshold),
        rag_top_k=int(settings.qdi_rag_top_k),
        policy_version=pv,
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


def get_comparar_questionario_diagnosticos_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> "CompararQuestionarioDiagnosticos":
    from src.application.use_cases.comparar_questionario_diagnosticos import (
        CompararQuestionarioDiagnosticos,
    )

    return CompararQuestionarioDiagnosticos(repo=repo)


def get_backfill_respostas_questionario_use_case() -> "BackfillRespostasQuestionario":
    import asyncio

    from src.application.use_cases.backfill_respostas_questionario import (
        BackfillRespostasQuestionario,
    )
    from src.infrastructure.config.settings import get_settings
    from src.infrastructure.repositories.postgres_backfill_respostas_questionario_sync import (
        buscar_payload_rascunho_para_backfill_sync,
        listar_diagnosticos_sem_respostas_sync,
        persistir_linhas_backfill_sync,
    )

    settings = get_settings()
    dsn = settings.sync_database_url or ""

    async def listar(tenant_id, *, limite: int):
        return await asyncio.to_thread(
            listar_diagnosticos_sem_respostas_sync, dsn, tenant_id, limite=limite
        )

    async def buscar_payload(did, tid, *, janela_horas: int):
        return await asyncio.to_thread(
            buscar_payload_rascunho_para_backfill_sync,
            dsn,
            did,
            tid,
            janela_horas=janela_horas,
        )

    async def persistir(did, tid, linhas):
        return await asyncio.to_thread(
            persistir_linhas_backfill_sync, dsn, did, tid, linhas
        )

    return BackfillRespostasQuestionario(
        listar_sem_respostas=listar,
        buscar_payload_rascunho=buscar_payload,
        persistir_linhas=persistir,
    )


def get_realizar_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    score_use_case: Annotated[CalcularScoreUseCase, Depends(get_calcular_score_use_case)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(get_pdf_generator)],
    storage_service: Annotated[SupabaseStorageAdapter, Depends(get_storage_service)],
    email_service: Annotated[SmtpEmailAdapter, Depends(get_email_service)],
    llm_gateway: Annotated[LlmGateway, Depends(get_llm_gateway_operacional)],
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
        llm_gateway=llm_gateway,
        base_normativa_port=base_normativa_port,
        cnpj_consulta_service=_cnpj_consulta_service_optional(),
        empresa_painel_arquivo_port=get_empresa_painel_arquivo_port(),
    )
