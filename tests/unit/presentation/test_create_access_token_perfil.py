"""Cobertura de normalização de `perfil_conta` em `create_access_token`."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import jwt

from src.presentation.api.routers.auth_router import create_access_token


def test_create_access_token_perfil_desconhecido_vira_gratuito_no_payload() -> None:
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!")
    m = MagicMock()
    m.jwt_secret_key.get_secret_value.return_value = secret
    m.jwt_algorithm = "HS256"
    uid = uuid4()
    tid = uuid4()
    with patch("src.presentation.api.routers.auth_router.deps.get_settings", return_value=m):
        token = create_access_token(
            subject_user_id=uid,
            tenant_id=tid,
            perfil_conta="  plano_inexistente  ",
        )
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    assert payload["perfil_conta"] == "gratuito"
