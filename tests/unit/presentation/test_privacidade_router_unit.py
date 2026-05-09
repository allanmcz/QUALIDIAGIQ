"""Testes do router LGPD — conversão defensiva e erros de caso de uso."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_registrar_solicitacao_titular_lgpd_use_case,
)
from src.presentation.api.main import app
from src.presentation.api.routers.privacidade_router import _to_response
from tests.conftest import cabecalho_auth_bearer

client = TestClient(app)


class TestPrivacidadeRouterUnit:
    """Ramos pouco exercitados em integração (tipo errado, ValueError)."""

    def test_to_response_rejeita_modelo_errado(self) -> None:
        with pytest.raises(TypeError, match="inválido"):
            _to_response(object())

    def test_registrar_solicitacao_use_case_value_error_400(self) -> None:
        uid, tid = uuid4(), uuid4()
        mock_uc = MagicMock()
        mock_uc.execute = AsyncMock(
            side_effect=ValueError("Diagnóstico não encontrado para o tenant.")
        )

        app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
        app.dependency_overrides[get_registrar_solicitacao_titular_lgpd_use_case] = lambda: mock_uc
        try:
            res = client.post(
                "/privacidade/solicitacoes",
                headers={
                    **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                    "Idempotency-Key": str(uuid4()),
                },
                json={
                    "tipo": "acesso",
                    "canal": "plataforma",
                    "solicitante_email": "titular@empresa.com",
                    "payload": {},
                },
            )
            assert res.status_code == 400
            assert "não encontrado" in res.json()["detail"].lower()
        finally:
            app.dependency_overrides.pop(get_current_user_tenant, None)
            app.dependency_overrides.pop(get_registrar_solicitacao_titular_lgpd_use_case, None)
