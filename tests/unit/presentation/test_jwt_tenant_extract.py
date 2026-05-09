"""Testes — ``tenant_id_from_bearer_authorization`` (idempotência multi-tenant best-effort)."""

from __future__ import annotations

import os
import uuid

import jwt
import pytest

from src.presentation.api.jwt_tenant_extract import (
    NIL_TENANT_ID,
    tenant_id_from_bearer_authorization,
)

_JWT_SECRET = os.environ["JWT_SECRET_KEY"]
_ALGO = ["HS256"]


@pytest.mark.parametrize(
    "header",
    [None, "", "   ", "Basic xxx", "bearertoken-sem-espaco"],
)
def test_nil_quando_sem_bearer_valido(header: str | None) -> None:
    assert tenant_id_from_bearer_authorization(header, _JWT_SECRET, _ALGO) == NIL_TENANT_ID


def test_nil_bearer_sem_token_apos_prefixo() -> None:
    assert tenant_id_from_bearer_authorization("Bearer ", _JWT_SECRET, _ALGO) == NIL_TENANT_ID
    assert tenant_id_from_bearer_authorization("Bearer   ", _JWT_SECRET, _ALGO) == NIL_TENANT_ID


def test_nil_jwt_sem_claim_tenant_id() -> None:
    token = jwt.encode({"sub": str(uuid.uuid4())}, _JWT_SECRET, algorithm="HS256")
    assert (
        tenant_id_from_bearer_authorization(f"Bearer {token}", _JWT_SECRET, _ALGO) == NIL_TENANT_ID
    )


def test_ok_quando_tenant_id_presente() -> None:
    tid = uuid.uuid4()
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "tenant_id": str(tid)}, _JWT_SECRET, algorithm="HS256"
    )
    assert tenant_id_from_bearer_authorization(f"Bearer {token}", _JWT_SECRET, _ALGO) == tid
