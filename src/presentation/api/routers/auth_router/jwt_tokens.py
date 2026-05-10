"""Emissão de JWT (painel e self-service)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from src.presentation.api.dependencies import SELF_SERVICE_DIAGNOSTICO_SCOPE

from . import deps


def create_access_token(
    *,
    subject_user_id: UUID,
    tenant_id: UUID,
    perfil_conta: str = "gratuito",
    expires_delta: timedelta | None = None,
) -> str:
    """Gera JWT com `sub` (id do admin), `tenant_id` e `perfil_conta` (conta na plataforma)."""
    settings = deps.get_settings()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )
    perfil = perfil_conta.strip().lower()
    if perfil not in ("gratuito", "avancado", "admin"):
        perfil = "gratuito"
    payload: dict[str, Any] = {
        "sub": str(subject_user_id),
        "tenant_id": str(tenant_id),
        "perfil_conta": perfil,
        "exp": expire,
    }
    return deps.jwt.encode(
        payload, settings.jwt_secret_key.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def create_self_service_access_token(*, email_norm: str) -> tuple[str, int]:
    """JWT de curta duração para gravar diagnóstico no tenant self-service após OTP."""
    settings = deps.get_settings()
    minutes = settings.self_service_jwt_expire_minutes
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    payload_jwt: dict[str, Any] = {
        "sub": str(uuid4()),
        "tenant_id": str(settings.self_service_tenant_id),
        "email": email_norm,
        "scope": SELF_SERVICE_DIAGNOSTICO_SCOPE,
        "exp": expire,
    }
    token = deps.jwt.encode(
        payload_jwt,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return token, int(minutes * 60)
