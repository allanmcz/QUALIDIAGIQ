"""Testes HTTP de POST /auth/login — ramos Postgres, erros de credencial e de integração."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import jwt
import psycopg2
import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from src.infrastructure.config.settings import get_settings
from src.presentation.api.main import app


@pytest.fixture(autouse=True)
def _limpar_settings() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _jwt_settings() -> MagicMock:
    m = MagicMock()
    m.sync_database_url = "postgresql://postgres:postgres@127.0.0.1:60322/postgres"
    m.jwt_expire_minutes = 60
    m.jwt_algorithm = "HS256"
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!")
    m.jwt_secret_key = MagicMock()
    m.jwt_secret_key.get_secret_value.return_value = secret
    return m


def _usuario_valido_bcryp(
    *,
    uid: UUID | None = None,
    tid: UUID | None = None,
    email: str = "login@teste.com",
    password: str = "senha12345",
    perfil_conta: str = "gratuito",
    nome: str | None = " Consultor ",
) -> tuple[dict, str]:
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash(password)
    uid = uid or uuid4()
    tid = tid or uuid4()
    row: dict = {
        "id": str(uid),
        "tenant_id": str(tid),
        "email": email,
        "hashed_password": hashed,
        "nome": nome,
        "perfil_conta": perfil_conta,
    }
    return row, password


class TestAuthLoginPostgres:
    """Fluxo síncrono com ``DATABASE_URL`` (paridade Compose/CI)."""

    def test_login_200_credenciais_validas(self) -> None:
        user, pwd = _usuario_valido_bcryp()
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("token_type") == "bearer"
        assert body.get("perfil_conta") == "gratuito"
        assert isinstance(body.get("access_token"), str)

    def test_login_400_usuario_inexistente(self) -> None:
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": "none@teste.com", "password": "xx"},
            )
        assert r.status_code == 400

    def test_login_400_senha_incorreta(self) -> None:
        user, _ = _usuario_valido_bcryp(password="certa")
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": "outra_senha_errada"},
            )
        assert r.status_code == 400

    def test_login_500_sem_hash_de_senha(self) -> None:
        user, pwd = _usuario_valido_bcryp()
        user["hashed_password"] = None
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500

    def test_login_500_hash_bcrypt_invalido(self) -> None:
        """bcrypt/passlib incompatibility ⇒ 500 com mensagem operacional."""

        user, pwd = _usuario_valido_bcryp()
        user["hashed_password"] = "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500
        assert "bcrypt" in (r.json().get("detail") or "").lower()

    def test_login_500_sem_tenant_no_registro(self) -> None:
        user, pwd = _usuario_valido_bcryp()
        user["tenant_id"] = None
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500

    def test_login_500_uuid_invalido_no_registro(self) -> None:
        user, pwd = _usuario_valido_bcryp()
        user["tenant_id"] = "nao-e-uuid"
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500

    def test_login_perfis_normalize_para_gratuito(self) -> None:
        user, pwd = _usuario_valido_bcryp(perfil_conta="  PLANINHO_FANTASMA ")
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 200
        assert r.json().get("perfil_conta") == "gratuito"

    def test_login_avancado_persistido(self) -> None:
        user, pwd = _usuario_valido_bcryp(perfil_conta="avancado")
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 200
        assert r.json().get("perfil_conta") == "avancado"

    def test_login_503_postgres_indisponivel(self) -> None:
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                side_effect=psycopg2.OperationalError("db down"),
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": "a@b.com", "password": "x"},
            )
        assert r.status_code == 503

    def test_login_supabase_quando_sem_dsn(self) -> None:
        """Sem ``sync_database_url`` o login consulta REST ``admins`` via Supabase client."""

        user, pwd = _usuario_valido_bcryp(email="sb@tst.io")
        settings = MagicMock()
        settings.sync_database_url = None
        settings.jwt_expire_minutes = 60
        settings.jwt_algorithm = "HS256"
        settings.jwt_secret_key = MagicMock()
        settings.jwt_secret_key.get_secret_value.return_value = os.environ.get(
            "JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!"
        )

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[user])
        )

        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.get_supabase_client",
                return_value=mock_client,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 200
        mock_client.table.assert_called_with("admins")

    def test_login_supabase_sem_resultados_400(self) -> None:
        """``response.data`` vazio ⇒ mesmo fluxo que utilizador inexistente."""
        settings = MagicMock()
        settings.sync_database_url = None
        settings.jwt_expire_minutes = 60
        settings.jwt_algorithm = "HS256"
        settings.jwt_secret_key = MagicMock()
        settings.jwt_secret_key.get_secret_value.return_value = os.environ.get(
            "JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!"
        )

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            MagicMock(data=[])
        )

        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.get_supabase_client",
                return_value=mock_client,
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": "naoexiste@sb.io", "password": "qualquer"},
            )
        assert r.status_code == 400

    def test_login_500_jwt_encode_falha(self) -> None:
        user, pwd = _usuario_valido_bcryp()
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
            patch(
                "src.presentation.api.routers.auth_router.jwt.encode", side_effect=Exception("x")
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500

    def test_login_500_pyjwt_na_emissao(self) -> None:
        """Falhas do PyJWT durante ``create_access_token`` viram HTTP 500 dedicado."""

        user, pwd = _usuario_valido_bcryp()
        settings = _jwt_settings()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=user,
            ),
            patch(
                "src.presentation.api.routers.auth_router.create_access_token",
                side_effect=jwt.DecodeError("erro sintético de emissão"),
            ),
        ):
            r = TestClient(app).post(
                "/auth/login",
                json={"email": user["email"], "password": pwd},
            )
        assert r.status_code == 500
        assert "jwt" in (r.json().get("detail") or "").lower()
