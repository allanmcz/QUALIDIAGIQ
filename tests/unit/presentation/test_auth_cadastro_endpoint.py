"""Testes HTTP de POST /auth/cadastro (mocks de Postgres e settings)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.config.settings import get_settings
from src.presentation.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _limpar_settings() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _settings_com_dsn() -> MagicMock:
    m = MagicMock()
    m.cadastro_consultor_b2b_habilitado = True
    m.sync_database_url = "postgresql://postgres:postgres@127.0.0.1:60322/postgres"
    m.jwt_expire_minutes = 60
    m.jwt_algorithm = "HS256"
    m.jwt_secret_key = MagicMock()
    m.jwt_secret_key.get_secret_value.return_value = os.environ.get(
        "JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!"
    )
    return m


class TestAuthCadastroEndpoint:
    """Fluxo feliz e erros de negócio."""

    def test_cadastro_201_retorna_token(self) -> None:
        uid = uuid4()
        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                return_value=uid,
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={
                    "nome": "Tester",
                    "email": "novo_cadastro_e2e@teste.com",
                    "password": "senha1234",
                },
            )
        assert r.status_code == 201, r.text
        body = r.json()
        assert body.get("token_type") == "bearer"
        assert isinstance(body.get("access_token"), str)
        assert body.get("perfil_conta") == "gratuito"

    def test_cadastro_403_quando_desabilitado(self) -> None:
        m = _settings_com_dsn()
        m.cadastro_consultor_b2b_habilitado = False
        with patch("src.presentation.api.routers.auth_router.get_settings", return_value=m):
            r = client.post(
                "/auth/cadastro",
                json={"nome": "A", "email": "b@c.com", "password": "12345678"},
            )
        assert r.status_code == 403

    def test_cadastro_409_email_existente(self) -> None:
        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value={"id": "x"},
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={"nome": "A", "email": "existente@teste.com", "password": "12345678"},
            )
        assert r.status_code == 409

    def test_cadastro_400_valueerror_inserir_sem_mensagem_duplicado(self) -> None:
        """ValueError de inserir sem palavra-chave de duplicidade → 400."""

        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                side_effect=ValueError("regra de negócio genérica"),
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={"nome": "A", "email": "unico_val@teste.com", "password": "12345678"},
            )
        assert r.status_code == 400
        assert "regra" in (r.json().get("detail") or "").lower()

    def test_cadastro_409_valueerror_duplicado_explicito_na_mensagem(self) -> None:
        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                side_effect=ValueError("registro já cadastrado na base"),
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={
                    "nome": "Dup",
                    "email": "dup_explicito@teste.com",
                    "password": "12345678",
                },
            )
        assert r.status_code == 409

    def test_cadastro_500_jwt_emit_erro_apos_insert(self) -> None:
        import jwt

        uid = uuid4()
        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                return_value=uid,
            ),
            patch(
                "src.presentation.api.routers.auth_router.create_access_token",
                side_effect=jwt.InvalidAudienceError("falha de teste"),
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={
                    "nome": "Jwt",
                    "email": "jwt_fail@teste.com",
                    "password": "12345678",
                },
            )
        assert r.status_code == 500
        assert "token" in (r.json().get("detail") or "").lower()

    def test_cadastro_409_excecao_generica_com_unique_na_mensagem(self) -> None:
        """Ramo ``except Exception`` com erro de unicidade ⇒ 409."""

        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_settings_com_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                return_value=uuid4(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.create_access_token",
                side_effect=RuntimeError("duplicate unique key value violates"),
            ),
        ):
            r = client.post(
                "/auth/cadastro",
                json={"nome": "A", "email": "uniq_ex@test.com", "password": "12345678"},
            )
        assert r.status_code == 409
