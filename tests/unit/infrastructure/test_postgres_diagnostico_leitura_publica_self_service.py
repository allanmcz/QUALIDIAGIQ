"""Testes do store síncrono de token de leitura pública pós-self-service (mock de psycopg2)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    buscar_diagnostico_conclusao_publica_sync,
    inserir_leitura_publica_self_service_sync,
)


@pytest.fixture
def mock_conn() -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = MagicMock()
    conn.cursor.return_value.__exit__.return_value = False
    return conn


def test_inserir_leitura_insere_e_devolve_token(mock_conn: MagicMock) -> None:
    cur = mock_conn.cursor.return_value.__enter__.return_value

    with patch(
        "src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service.psycopg2.connect",
        return_value=mock_conn,
    ):
        tok = inserir_leitura_publica_self_service_sync(
            "postgresql://test",
            uuid4(),
            uuid4(),
        )

    assert len(tok) >= 32
    cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def test_buscar_conclusao_sem_token_retorna_none(mock_conn: MagicMock) -> None:
    diag_id = uuid4()
    tenant_id = uuid4()

    cur = MagicMock()
    cur.fetchone.return_value = None
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = False
    mock_conn.cursor.return_value = cm

    with patch(
        "src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service.psycopg2.connect",
        return_value=mock_conn,
    ):
        out = buscar_diagnostico_conclusao_publica_sync(
            "postgresql://test",
            diagnostico_id=diag_id,
            tenant_id_esperado=tenant_id,
            token_plain="x" * 32,
        )

    assert out is None
    mock_conn.close.assert_called_once()


def test_buscar_conclusao_com_token_retorna_linha(mock_conn: MagicMock) -> None:
    diag_id = uuid4()
    tenant_id = uuid4()

    cur1 = MagicMock()
    cur1.fetchone.return_value = {"x": 1}
    cm1 = MagicMock()
    cm1.__enter__.return_value = cur1
    cm1.__exit__.return_value = False

    cur2 = MagicMock()
    cur2.fetchone.return_value = {
        "id": str(diag_id),
        "status": "finalizado",
        "empresa_razao_social": "Empresa Mock",
        "locale_relatorio": "pt-BR",
        "score_completo": None,
    }
    cm2 = MagicMock()
    cm2.__enter__.return_value = cur2
    cm2.__exit__.return_value = False

    mock_conn.cursor.side_effect = [cm1, cm2]

    with patch(
        "src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service.psycopg2.connect",
        return_value=mock_conn,
    ):
        out = buscar_diagnostico_conclusao_publica_sync(
            "postgresql://test",
            diagnostico_id=diag_id,
            tenant_id_esperado=tenant_id,
            token_plain="y" * 32,
        )

    assert out is not None
    assert out["empresa_razao_social"] == "Empresa Mock"
    mock_conn.close.assert_called_once()
