"""
Rotas de autenticação B2B.

Camada: Presentation
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

import jwt
import structlog
from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from src.infrastructure.config.settings import get_settings
from src.presentation.api.dependencies import get_supabase_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticação B2B"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    nome: str | None


def create_access_token(
    *,
    subject_user_id: UUID,
    tenant_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Gera JWT com `sub` (id do admin) e claim `tenant_id`."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )
    payload: dict[str, Any] = {
        "sub": str(subject_user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Login contra a tabela `admins`; token inclui tenant para RLS futuro."""
    client = get_supabase_client()

    try:
        response = client.table("admins").select("*").eq("email", str(request.email)).execute()
        users = response.data
        if not users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail ou senha incorretos",
            )

        user = cast("dict[str, Any]", users[0])
        if not pwd_context.verify(request.password, str(user["hashed_password"])):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail ou senha incorretos",
            )

        raw_tid = user.get("tenant_id")
        if raw_tid is None:
            logger.error("admin_sem_tenant_id", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuração de tenant ausente para este usuário",
            )

        tenant_id = UUID(str(raw_tid))
        user_id = UUID(str(user["id"]))

        settings = get_settings()
        access_token = create_access_token(
            subject_user_id=user_id,
            tenant_id=tenant_id,
            expires_delta=timedelta(minutes=settings.jwt_expire_minutes),
        )
        nome_raw = user.get("nome")
        nome = str(nome_raw) if nome_raw is not None else None
        return LoginResponse(access_token=access_token, token_type="bearer", nome=nome)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("login_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao autenticar",
        ) from e
