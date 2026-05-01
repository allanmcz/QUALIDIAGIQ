"""
Configuração de Injeção de Dependências e Segurança.

Camada: Presentation (FastAPI)
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.infrastructure.adapters.email_smtp import SmtpEmailAdapter
from src.infrastructure.adapters.llm_ollama import OllamaLlmAdapter
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter
from src.infrastructure.config.settings import get_settings
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
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


def get_calcular_score_use_case() -> CalcularScoreUseCase:
    """Injeta o motor matemático de Score."""
    return CalcularScoreUseCase()


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
