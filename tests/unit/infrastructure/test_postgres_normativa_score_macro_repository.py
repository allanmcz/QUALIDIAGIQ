"""Testes unitários do repositório Postgres de pesos macro (sem container)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import psycopg2.errors
import pytest

from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.postgres_normativa_score_macro_repository import (
    PostgresNormativaScoreMacroRepository,
)


class TestPostgresNormativaScoreMacroRepository:
    """Mapeia falhas de conexão, migração ausente e dimensão desconhecida."""

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
        side_effect=Exception("offline"),
    )
    def test_conexao_falha_runtime_error(self, _mock_connect: MagicMock) -> None:
        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        with pytest.raises(RuntimeError, match="Falha ao conectar"):
            repo.obter_pesos_macro_validos_na_data(date(2026, 5, 9))

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_tabela_ausente_runtime_error(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.execute.side_effect = psycopg2.errors.UndefinedTable("missing")
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        with pytest.raises(RuntimeError, match="normativa_score_macro_dimensao"):
            repo.obter_pesos_macro_validos_na_data(date(2026, 1, 1))
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_obter_pesos_macro_retorna_mapa(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [("fiscal", 1.5)]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        out = repo.obter_pesos_macro_validos_na_data(date(2026, 1, 1))
        assert out[Dimensao.FISCAL] == 1.5
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_dimensao_desconhecida_value_error(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [("slug_inexistente", 1.5)]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        with pytest.raises(ValueError, match="Dimensão desconhecida"):
            repo.obter_pesos_macro_validos_na_data(date(2026, 1, 1))
