"""
Autenticação JWT (painel e self-service) e cliente Supabase singleton.

Camada: Presentation (FastAPI)

Extraído de ``dependencies.py`` (Onda 2 refactor) para reduzir tamanho do módulo
agregador; rotas e testes continuam a importar símbolos reexportados em
``dependencies``.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from src.domain.value_objects.email import normalizar_email
from src.infrastructure.config.settings import get_settings

logger = structlog.get_logger(__name__)

_supabase_client: Client | None = None

bearer_scheme = HTTPBearer(auto_error=False)

SELF_SERVICE_DIAGNOSTICO_SCOPE = "self_service_diagnostico"


def reset_supabase_client_singleton() -> None:
    """Limpa memoização do cliente Supabase (testes / recarga controlada)."""
    global _supabase_client
    _supabase_client = None


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
) -> tuple[UUID, UUID, str]:
    """
    Valida Bearer JWT e retorna (user_id, tenant_id, perfil_conta).

    Claims esperadas: `sub` = UUID do admin, `tenant_id` = UUID do tenant,
    `perfil_conta` opcional (`gratuito` | `avancado` | `admin`; tokens antigos assumem gratuito).
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
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        tid = payload.get("tenant_id")
        if not sub or not tid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token sem subject ou tenant_id",
            )
        perfil_raw = payload.get("perfil_conta") or "gratuito"
        perfil = str(perfil_raw).strip().lower()
        if perfil not in ("gratuito", "avancado", "admin"):
            perfil = "gratuito"
        return UUID(str(sub)), UUID(str(tid)), perfil
    except HTTPException:
        raise
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning("jwt_invalido", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from e


async def require_perfil_manutencao_plataforma(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
) -> tuple[UUID, UUID, str]:
    """
    Operações de manutenção (limpeza idempotência, etc.).

    Aceita perfil **admin** (operador plataforma) ou **avancado** (compatível com contas
    privilegiadas até perfil dedicado estar generalizado).
    """
    _uid, _tid, perfil = current
    if perfil not in ("admin", "avancado"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação restrita a perfil de manutenção (admin ou avançado).",
        )
    return current


async def get_self_service_diagnostico_claims(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> tuple[UUID, UUID, str]:
    """
    JWT emitido por POST /auth/self-service/token após OTP válido.

    Returns:
        Tupla (subject_sessão, tenant_id, email_normalizado) para gravar diagnóstico no pool self-service.
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
            settings.jwt_secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except (jwt.PyJWTError, ValueError) as e:
        logger.warning("jwt_self_service_invalido", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from e

    if payload.get("scope") != SELF_SERVICE_DIAGNOSTICO_SCOPE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não autorizado para gravar diagnóstico self-service",
        )

    sub = payload.get("sub")
    tid = payload.get("tenant_id")
    email_raw = payload.get("email")
    if not sub or not tid or not email_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token self-service incompleto",
        )
    try:
        tenant_uuid = UUID(str(tid))
        session_uuid = UUID(str(sub))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token self-service com identificadores inválidos",
        ) from e

    if tenant_uuid != settings.self_service_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant do token incompatível com self-service",
        )

    email_norm = normalizar_email(str(email_raw))
    return session_uuid, tenant_uuid, email_norm
