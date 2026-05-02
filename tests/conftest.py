"""Fixtures globais — JWT de teste e cache de Settings."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!")
os.environ.setdefault("APP_ENV", "development")


@pytest.fixture(autouse=True)
def _limpar_cache_settings() -> None:
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _limpar_cache_idempotencia() -> None:
    """Evita que replay de idempotência vaze entre testes."""
    from src.presentation.api.main import app

    def _clear() -> None:
        cache = getattr(app.state, "idempotency_cache", None)
        if cache is not None:
            cache.clear()

    _clear()
    yield
    _clear()


def cabecalho_auth_bearer(
    *,
    usuario_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
) -> dict[str, str]:
    """Authorization Bearer com claims `sub` e `tenant_id` (mesmo contrato da API)."""
    uid = usuario_id if usuario_id is not None else uuid.uuid4()
    tid = tenant_id if tenant_id is not None else uuid.uuid4()
    secret = os.environ["JWT_SECRET_KEY"]
    token = jwt.encode(
        {
            "sub": str(uid),
            "tenant_id": str(tid),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def cabecalho_post_diagnostico(
    *,
    usuario_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """Bearer + Idempotency-Key (obrigatório para POST /diagnosticos/)."""
    return {
        **cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id),
        "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
    }


def cabecalho_post_diagnostico_self_service(
    *,
    email: str,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """Bearer JWT self-service (OTP) + Idempotency-Key para POST /diagnosticos/self-service."""
    from src.infrastructure.config.settings import get_settings
    from src.presentation.api.dependencies import SELF_SERVICE_DIAGNOSTICO_SCOPE

    settings = get_settings()
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tenant_id": str(settings.self_service_tenant_id),
            "email": email.strip().lower(),
            "scope": SELF_SERVICE_DIAGNOSTICO_SCOPE,
            "exp": datetime.now(UTC) + timedelta(minutes=30),
        },
        os.environ["JWT_SECRET_KEY"],
        algorithm="HS256",
    )
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key or str(uuid.uuid4()),
    }
