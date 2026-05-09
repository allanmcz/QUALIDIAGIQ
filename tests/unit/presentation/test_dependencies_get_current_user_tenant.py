"""Ramos de JWT do painel em ``get_current_user_tenant``."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from src.presentation.api.dependencies import get_current_user_tenant


@pytest.mark.asyncio
async def test_sem_claim_sub_retorna_401() -> None:
    secret = os.environ["JWT_SECRET_KEY"]
    tid = uuid4()
    tok = jwt.encode(
        {"tenant_id": str(tid), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        secret,
        algorithm="HS256",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)
    with pytest.raises(HTTPException) as ei:
        await get_current_user_tenant(creds)
    assert ei.value.status_code == 401
    assert "subject" in ei.value.detail


@pytest.mark.asyncio
async def test_sem_claim_tenant_id_retorna_401() -> None:
    secret = os.environ["JWT_SECRET_KEY"]
    uid = uuid4()
    tok = jwt.encode(
        {"sub": str(uid), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        secret,
        algorithm="HS256",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)
    with pytest.raises(HTTPException) as ei:
        await get_current_user_tenant(creds)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_perfil_conta_desconhecido_normaliza_gratuito() -> None:
    secret = os.environ["JWT_SECRET_KEY"]
    uid, tid = uuid4(), uuid4()
    tok = jwt.encode(
        {
            "sub": str(uid),
            "tenant_id": str(tid),
            "perfil_conta": "plano_xyz_inexistente",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=tok)
    _, _, perfil = await get_current_user_tenant(creds)
    assert perfil == "gratuito"


@pytest.mark.asyncio
async def test_scheme_basic_rejeita_401() -> None:
    tok = jwt.encode({}, "ignored", algorithm="HS256")  # corpo irrelevante sem Bearer
    creds = HTTPAuthorizationCredentials(scheme="Basic", credentials=tok)
    with pytest.raises(HTTPException) as ei:
        await get_current_user_tenant(creds)
    assert ei.value.status_code == 401
