"""Testes de ``jwt_llm_tier_context`` — extracção segura do JWT."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from src.presentation.api.jwt_llm_tier_context import llm_tier_context_from_authorization


class TestJwtLlmTierContext:
    """Só Bearer assinado; sem header → vazio."""

    def test_sem_authorization(self) -> None:
        assert llm_tier_context_from_authorization(
            None, jwt_secret="k" * 32, algorithms=["HS256"]
        ) == (None, None)

    def test_bearer_invalido(self) -> None:
        assert llm_tier_context_from_authorization(
            "Token x", jwt_secret="k" * 32, algorithms=["HS256"]
        ) == (None, None)

    def test_bearer_sem_token_apos_prefixo(self) -> None:
        assert llm_tier_context_from_authorization(
            "Bearer ", jwt_secret="k" * 32, algorithms=["HS256"]
        ) == (None, None)

    def test_token_assinatura_invalida(self) -> None:
        assert llm_tier_context_from_authorization(
            "Bearer nao-eh-jwt.valido", jwt_secret="k" * 32, algorithms=["HS256"]
        ) == (None, None)
        secret = "z" * 32
        exp = datetime.now(UTC) + timedelta(hours=1)
        payload = {
            "sub": str(uuid4()),
            "tenant_id": str(uuid4()),
            "perfil_conta": "avancado",
            "qdi_llm_tier": "premium",
            "exp": exp,
        }
        tok = jwt.encode(payload, secret, algorithm="HS256")
        c, p = llm_tier_context_from_authorization(
            f"Bearer {tok}", jwt_secret=secret, algorithms=["HS256"]
        )
        assert c == "premium"
        assert p == "avancado"
