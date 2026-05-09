"""POST /auth/cadastro quando não há DATABASE_URL síncrono (ramo Supabase mockado)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.infrastructure.config.settings import get_settings
from src.presentation.api.main import app


def _jwt_settings_sem_dsn(*, cadastro_habilitado: bool = True) -> MagicMock:
    m = MagicMock()
    m.cadastro_consultor_b2b_habilitado = cadastro_habilitado
    m.sync_database_url = None
    m.jwt_expire_minutes = 60
    m.jwt_algorithm = "HS256"
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!")
    m.jwt_secret_key = MagicMock()
    m.jwt_secret_key.get_secret_value.return_value = secret
    return m


class TestCadastroConsultorBranchSupabase:
    """Mocks de ``client.table("admins")`` sem Postgres."""

    def test_cadastro_201_via_supabase(self) -> None:
        get_settings.cache_clear()
        mock_tbl = MagicMock()
        mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        new_id = uuid4()
        mock_tbl.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": str(new_id)}],
        )
        mock_client = MagicMock()
        mock_client.table.return_value = mock_tbl

        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_jwt_settings_sem_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.get_supabase_client",
                return_value=mock_client,
            ),
        ):
            r = TestClient(app).post(
                "/auth/cadastro",
                json={
                    "nome": "Via Supabase",
                    "email": "supa_route@test.io",
                    "password": "12345678",
                },
            )
        get_settings.cache_clear()
        assert r.status_code == 201
        mock_client.table.assert_called_with("admins")

    def test_cadastro_409_email_duplicado_supabase(self) -> None:
        get_settings.cache_clear()
        mock_tbl = MagicMock()
        mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "x"}],
        )
        mock_client = MagicMock()
        mock_client.table.return_value = mock_tbl

        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_jwt_settings_sem_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.get_supabase_client",
                return_value=mock_client,
            ),
        ):
            r = TestClient(app).post(
                "/auth/cadastro",
                json={"nome": "A", "email": "dup@supa.io", "password": "12345678"},
            )
        get_settings.cache_clear()
        assert r.status_code == 409

    def test_cadastro_500_insert_sem_linha_retornada(self) -> None:
        get_settings.cache_clear()
        mock_tbl = MagicMock()
        mock_tbl.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_tbl.insert.return_value.execute.return_value = MagicMock(data=None)
        mock_client = MagicMock()
        mock_client.table.return_value = mock_tbl

        with (
            patch(
                "src.presentation.api.routers.auth_router.get_settings",
                return_value=_jwt_settings_sem_dsn(),
            ),
            patch(
                "src.presentation.api.routers.auth_router.get_supabase_client",
                return_value=mock_client,
            ),
        ):
            r = TestClient(app).post(
                "/auth/cadastro",
                json={"nome": "A", "email": "emp@supa.io", "password": "12345678"},
            )
        get_settings.cache_clear()
        assert r.status_code == 500

    def test_cadastro_503_postgres_indisponivel_postgres_ramificacao(self) -> None:
        """``inserir_admin_postgres`` propaga OperationalError ⇒ 503."""
        import psycopg2

        settings = MagicMock()
        settings.cadastro_consultor_b2b_habilitado = True
        settings.sync_database_url = "postgresql://x:y@127.0.0.1:1/x"
        settings.jwt_expire_minutes = 60
        settings.jwt_algorithm = "HS256"
        settings.jwt_secret_key = MagicMock()
        settings.jwt_secret_key.get_secret_value.return_value = os.environ.get(
            "JWT_SECRET_KEY", "test-secret-key-for-pytest-only-32chars!!"
        )

        get_settings.cache_clear()
        with (
            patch("src.presentation.api.routers.auth_router.get_settings", return_value=settings),
            patch(
                "src.presentation.api.routers.auth_router.buscar_admin_por_email_postgres",
                return_value=None,
            ),
            patch(
                "src.presentation.api.routers.auth_router.inserir_admin_postgres",
                side_effect=psycopg2.OperationalError("simulated"),
            ),
        ):
            r = TestClient(app).post(
                "/auth/cadastro",
                json={"nome": "A", "email": "pg503@test.io", "password": "12345678"},
            )
        get_settings.cache_clear()
        assert r.status_code == 503
