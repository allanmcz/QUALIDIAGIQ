"""Ramos HTTP de ``get_self_service_diagnostico_claims`` fora das rotas (dependency isolada)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.infrastructure.config.settings import get_settings
from src.presentation.api import dependencies as deps


def _token_claims_hs256(secret: str, payload: dict) -> str:
    exp = datetime.now(UTC) + timedelta(hours=2)
    p = dict(payload)
    p["exp"] = int(exp.timestamp())
    return jwt.encode(p, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_self_service_claims_rejeita_scope_incompativel() -> None:
    get_settings.cache_clear()
    tid_ss = UUID("33333333-3333-4333-8333-333333333333")

    jwt_secret = "jwt-test-secret-deps-self-svc-32chars__"
    payload = _token_claims_hs256(
        jwt_secret,
        {
            "sub": str(uuid4()),
            "tenant_id": str(tid_ss),
            "email": "lead@test.io",
            "scope": "escopo_incorreto",
        },
    )

    mock_s = MagicMock()
    mock_s.self_service_tenant_id = tid_ss
    mock_s.jwt_secret_key.get_secret_value.return_value = jwt_secret
    mock_s.jwt_algorithm = "HS256"

    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=payload)

    with (
        patch("src.presentation.api.deps_auth_supabase.get_settings", return_value=mock_s),
        pytest.raises(HTTPException) as ei,
    ):
        await deps.get_self_service_diagnostico_claims(credentials=cred)

    assert ei.value.status_code == 403

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_self_service_claims_rejeita_tenant_divergente_do_pool() -> None:
    jwt_secret = "jwt-test-secret-deps-self-svc-33chars___"
    token = _token_claims_hs256(
        jwt_secret,
        {
            "sub": str(uuid4()),
            "tenant_id": str(uuid4()),
            "email": "x@y.com",
            "scope": deps.SELF_SERVICE_DIAGNOSTICO_SCOPE,
        },
    )

    mock_s = MagicMock()
    mock_s.self_service_tenant_id = UUID("44444444-4444-4444-8444-444444444444")
    mock_s.jwt_secret_key.get_secret_value.return_value = jwt_secret
    mock_s.jwt_algorithm = "HS256"

    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with (
        patch("src.presentation.api.deps_auth_supabase.get_settings", return_value=mock_s),
        pytest.raises(HTTPException) as ei,
    ):
        await deps.get_self_service_diagnostico_claims(credentials=cred)

    assert ei.value.status_code == 403


@pytest.mark.asyncio
async def test_self_service_claims_credencial_nao_e_bearer_401() -> None:
    cred = MagicMock(spec=HTTPAuthorizationCredentials)
    cred.scheme = "Basic"

    with pytest.raises(HTTPException) as ei:
        await deps.get_self_service_diagnostico_claims(credentials=cred)

    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_self_service_claims_token_exige_sub_tenant_email_completos() -> None:
    jwt_secret = "jwt-test-secret-deps-self-svc-34chars____"
    tid_ss = UUID("55555555-5555-4555-8555-555555555555")
    token_sem_email = jwt.encode(
        {
            "sub": str(uuid4()),
            "tenant_id": str(tid_ss),
            "scope": deps.SELF_SERVICE_DIAGNOSTICO_SCOPE,
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        jwt_secret,
        algorithm="HS256",
    )

    mock_s = MagicMock()
    mock_s.self_service_tenant_id = tid_ss
    mock_s.jwt_secret_key.get_secret_value.return_value = jwt_secret
    mock_s.jwt_algorithm = "HS256"

    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_sem_email)

    with (
        patch("src.presentation.api.deps_auth_supabase.get_settings", return_value=mock_s),
        pytest.raises(HTTPException) as ei,
    ):
        await deps.get_self_service_diagnostico_claims(credentials=cred)

    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_self_service_claims_uuid_invalidos_no_token_401() -> None:
    jwt_secret = "jwt-test-secret-deps-self-svc-35chars_____"
    tid_ss = UUID("66666666-6666-4666-8666-666666666666")
    token_bad = jwt.encode(
        {
            "sub": "uuid-invalido-sub",
            "tenant_id": str(tid_ss),
            "email": "ok@test.io",
            "scope": deps.SELF_SERVICE_DIAGNOSTICO_SCOPE,
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        jwt_secret,
        algorithm="HS256",
    )

    mock_s = MagicMock()
    mock_s.self_service_tenant_id = tid_ss
    mock_s.jwt_secret_key.get_secret_value.return_value = jwt_secret
    mock_s.jwt_algorithm = "HS256"

    cred = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_bad)

    with (
        patch("src.presentation.api.deps_auth_supabase.get_settings", return_value=mock_s),
        pytest.raises(HTTPException) as ei,
    ):
        await deps.get_self_service_diagnostico_claims(credentials=cred)

    assert ei.value.status_code == 401
