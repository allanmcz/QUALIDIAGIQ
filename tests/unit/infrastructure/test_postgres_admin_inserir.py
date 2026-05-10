"""Testes unitários de `inserir_admin_postgres` (mock de conexão)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.infrastructure.auth.postgres_admin_login import (
    buscar_admin_por_email_postgres,
    buscar_email_admin_por_id_e_tenant_postgres,
    inserir_admin_postgres,
)


class TestInserirAdminPostgres:
    """INSERT simulado — sem Postgres real."""

    def test_retorna_uuid_do_returning(self) -> None:
        novo = uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (str(novo),)
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            tid = uuid4()
            out = inserir_admin_postgres(
                email="novo@teste.com",
                hashed_password="hashfake",
                nome="Novo User",
                tenant_id=tid,
                dsn_sync="postgresql://u:p@localhost:1/db",
            )
        assert out == novo
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_unique_violation_vira_valueerror(self) -> None:
        import psycopg2.errors

        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = psycopg2.errors.UniqueViolation("dup")
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with (
            patch(
                "src.infrastructure.auth.postgres_admin_login.psycopg2.connect",
                return_value=mock_conn,
            ),
            pytest.raises(ValueError, match="cadastrado"),
        ):
            inserir_admin_postgres(
                email="dup@teste.com",
                hashed_password="h",
                nome="X",
                tenant_id=UUID("33333333-3333-4333-8333-333333333333"),
                dsn_sync="postgresql://u:p@localhost:1/db",
            )
        mock_conn.rollback.assert_called()

    def test_returning_sem_id_dispara_runtimeerror(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with (
            patch(
                "src.infrastructure.auth.postgres_admin_login.psycopg2.connect",
                return_value=mock_conn,
            ),
            pytest.raises(RuntimeError, match="não retornou"),
        ):
            inserir_admin_postgres(
                email="x@teste.com",
                hashed_password="h",
                nome="N",
                tenant_id=uuid4(),
                dsn_sync="postgresql://u:p@localhost:1/db",
            )
        mock_conn.rollback.assert_called()

    def test_erro_generico_faz_rollback_e_propaga(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = ConnectionError("indisponível")
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with (
            patch(
                "src.infrastructure.auth.postgres_admin_login.psycopg2.connect",
                return_value=mock_conn,
            ),
            pytest.raises(ConnectionError, match="indisponível"),
        ):
            inserir_admin_postgres(
                email="x@teste.com",
                hashed_password="h",
                nome="N",
                tenant_id=uuid4(),
                dsn_sync="postgresql://u:p@localhost:1/db",
            )
        mock_conn.rollback.assert_called()

    def test_perfil_invalido_grava_gratuito(self) -> None:
        novo = uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (str(novo),)
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            out = inserir_admin_postgres(
                email="p@teste.com",
                hashed_password="h",
                nome="N",
                tenant_id=uuid4(),
                dsn_sync="postgresql://u:p@localhost:1/db",
                perfil_conta="  PLANO_INEXISTENTE  ",
            )
        assert out == novo
        bind = mock_cursor.execute.call_args[0][1]
        assert isinstance(bind[3], str)
        assert bind[4] == "gratuito"

    def test_nome_somente_espacos_grava_none(self) -> None:
        novo = uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (str(novo),)
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            inserir_admin_postgres(
                email="esp@teste.com",
                hashed_password="h",
                nome="     ",
                tenant_id=uuid4(),
                dsn_sync="postgresql://u:p@localhost:1/db",
            )
        bind = mock_cursor.execute.call_args[0][1]
        assert bind[2] is None
        assert isinstance(bind[3], str)


class TestBuscarAdminPostgres:
    def test_buscar_admin_por_email_normaliza_e_retorna_dict(self) -> None:
        row = {
            "id": str(uuid4()),
            "email": "admin@teste.com",
            "hashed_password": "h",
            "nome": "Admin",
            "tenant_id": str(uuid4()),
            "perfil_conta": "gratuito",
        }
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = row
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            out = buscar_admin_por_email_postgres("  ADMIN@TESTE.COM  ", "postgresql://x")

        assert out is not None
        assert out["email"] == "admin@teste.com"
        bind = mock_cursor.execute.call_args[0][1]
        assert bind == ("admin@teste.com",)
        mock_conn.close.assert_called_once()

    def test_buscar_admin_por_email_sem_linha_retorna_none(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            assert buscar_admin_por_email_postgres("x@teste.com", "postgresql://x") is None

        mock_conn.close.assert_called_once()

    def test_buscar_email_por_id_tenant_retorna_lower(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"email": "  ADMIN@TESTE.COM "}
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm
        admin_id = uuid4()
        tenant_id = uuid4()

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            out = buscar_email_admin_por_id_e_tenant_postgres(admin_id, tenant_id, "postgresql://x")

        assert out == "admin@teste.com"
        bind = mock_cursor.execute.call_args[0][1]
        assert bind == (str(admin_id), str(tenant_id))
        mock_conn.close.assert_called_once()

    def test_buscar_email_por_id_tenant_sem_linha_ou_email_retorna_none(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [None, {"email": None}]
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_cursor
        mock_cm.__exit__.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cm

        with patch(
            "src.infrastructure.auth.postgres_admin_login.psycopg2.connect", return_value=mock_conn
        ):
            assert (
                buscar_email_admin_por_id_e_tenant_postgres(uuid4(), uuid4(), "postgresql://x")
                is None
            )
            assert (
                buscar_email_admin_por_id_e_tenant_postgres(uuid4(), uuid4(), "postgresql://x")
                is None
            )
