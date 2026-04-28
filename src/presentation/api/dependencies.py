"""
Configuração de Injeção de Dependências e Segurança.

Camada: Presentation (FastAPI)
"""

import os
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from supabase import Client, create_client

from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)

# Cache global do client Supabase para a API
_supabase_client: Client | None = None


def get_tenant_id(
    x_tenant_id: Annotated[str | None, Header(description="ID do Tenant para isolamento")] = None,
) -> UUID:
    """Extrai e valida o cabeçalho X-Tenant-ID."""
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-Tenant-ID ausente",
        )
    try:
        return UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-Tenant-ID inválido (deve ser UUID)",
        )


def get_supabase_client() -> Client:
    """Instancia o cliente Supabase."""
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:60000")
        key = os.environ.get("SUPABASE_KEY", "dummy_key")
        _supabase_client = create_client(url, key)
    return _supabase_client


def get_diagnostico_repository(
    client: Annotated[Client, Depends(get_supabase_client)],
) -> SupabaseDiagnosticoRepository:
    """Injeta a implementação concreta do Repositório."""
    return SupabaseDiagnosticoRepository(client=client)


def get_calcular_score_use_case() -> CalcularScoreUseCase:
    """Injeta o motor matemático de Score."""
    return CalcularScoreUseCase()


def get_realizar_diagnostico_use_case(
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
    score_use_case: Annotated[CalcularScoreUseCase, Depends(get_calcular_score_use_case)],
) -> RealizarDiagnostico:
    """Orquestrador principal."""
    return RealizarDiagnostico(repo=repo, calcular_score_use_case=score_use_case)
