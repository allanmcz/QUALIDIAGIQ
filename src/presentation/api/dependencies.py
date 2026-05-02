"""
Configuração de Injeção de Dependências e Segurança.

Camada: Presentation (FastAPI)
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from src.application.use_cases.anexar_relatorio_otimista import AnexarRelatorioOtimista
from src.application.use_cases.atualizar_checklist_m12_autoconf import AtualizarChecklistM12Autoconf
from src.application.use_cases.buscar_cnae_subclasses import BuscarCnaeSubclasses
from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro
from src.infrastructure.adapters.email_smtp import SmtpEmailAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter
from src.infrastructure.config.settings import get_settings
from src.infrastructure.questionario.banco_cache import get_banco_perguntas_cached
from src.infrastructure.repositories.postgres_cnae_subclasse_repository import (
    PostgresCnaeSubclasseRepository,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)

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

_supabase_client: Client | None = None

bearer_scheme = HTTPBearer(auto_error=False)


def get_supabase_client() -> Client:
    """Instancia o cliente Supabase (singleton por processo)."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client


async def get_current_user_tenant(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> tuple[UUID, UUID]:
    """
    Valida Bearer JWT e retorna (user_id, tenant_id).

    Claims esperadas: `sub` = UUID do admin, `tenant_id` = UUID do tenant.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Bearer ausente ou inválido",
        )

    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        tid = payload.get("tenant_id")
        if not sub or not tid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sem subject ou tenant_id",
            )
        return UUID(str(sub)), UUID(str(tid))
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning("jwt_invalido", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from e


def get_diagnostico_repository(
    client: Annotated[Client, Depends(get_supabase_client)],
) -> SupabaseDiagnosticoRepository:
    """Injeta a implementação concreta do Repositório."""
    return SupabaseDiagnosticoRepository(client=client)


def get_anexar_relatorio_otimista_use_case(
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> AnexarRelatorioOtimista:
    """PATCH de relatório com versão otimista."""
    return AnexarRelatorioOtimista(repo=repo)


def get_atualizar_checklist_m12_autoconf_use_case(
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> AtualizarChecklistM12Autoconf:
    """PATCH M12 (autoconf ABNT) com versão otimista."""
    return AtualizarChecklistM12Autoconf(repo=repo)


def get_calcular_score_use_case() -> CalcularScoreUseCase:
    """Injeta o motor matemático de Score."""
    return CalcularScoreUseCase()


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


def get_llm_service() -> OllamaLlmAdapter:
    """Injeta o serviço de IA."""
    return OllamaLlmAdapter()


def get_buscar_cnae_subclasses_use_case(
    _auth: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
) -> BuscarCnaeSubclasses:
    """
    Lookup CNAE via Postgres (`DATABASE_URL`).

    RLS nas tabelas `qdi.*` aplica-se a roles Supabase; a API usa conexão de serviço
    tipicamente com permissão SELECT já concedida nas migrações 0013/0014.
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
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
    score_use_case: Annotated[CalcularScoreUseCase, Depends(get_calcular_score_use_case)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(get_pdf_generator)],
    storage_service: Annotated[SupabaseStorageAdapter, Depends(get_storage_service)],
    email_service: Annotated[SmtpEmailAdapter, Depends(get_email_service)],
    llm_service: Annotated[OllamaLlmAdapter, Depends(get_llm_service)],
) -> RealizarDiagnostico:
    """Orquestrador principal."""
    return RealizarDiagnostico(
        repo=repo,
        calcular_score_use_case=score_use_case,
        pdf_generator=pdf_generator,
        storage_service=storage_service,
        email_service=email_service,
        llm_service=llm_service,
    )
