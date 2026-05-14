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
        cur.fetchall.return_value = [
            ("fiscal", 1.5, date(2026, 1, 1), None, "baseline-test"),
            ("tecnologica", 1.3, date(2026, 1, 1), None, "baseline-test"),
            ("compliance_abnt_17301", 1.2, date(2026, 1, 1), None, "baseline-test"),
            ("estrategica", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("contabil", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("financeira", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("operacional", 1.0, date(2026, 1, 1), None, "baseline-test"),
        ]
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
    def test_obter_metadados_inclui_vigencia_e_rotulo(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("fiscal", 1.5, date(2026, 1, 1), None, "baseline-test"),
            ("tecnologica", 1.3, date(2026, 1, 1), None, "baseline-test"),
            ("compliance_abnt_17301", 1.2, date(2026, 1, 1), None, "baseline-test"),
            ("estrategica", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("contabil", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("financeira", 1.0, date(2026, 1, 1), None, "baseline-test"),
            ("operacional", 1.0, date(2026, 1, 1), None, "baseline-test"),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        meta = repo.obter_metadados_macro_validos_na_data(date(2026, 1, 1))
        assert meta[Dimensao.FISCAL].vigencia_inicio == date(2026, 1, 1)
        assert meta[Dimensao.FISCAL].rotulo_versao == "baseline-test"
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_obter_metadados_aceita_vigencia_como_string_iso(self, mock_connect: MagicMock) -> None:
        """Alguns drivers devolvem DATE como str — normalizamos para ``date``."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("fiscal", 1.5, "2026-01-01", None, "baseline-str"),
            ("tecnologica", 1.3, "2026-01-01", "2027-01-01", "baseline-str"),
            ("compliance_abnt_17301", 1.2, "2026-01-01", None, "baseline-str"),
            ("estrategica", 1.0, "2026-01-01", None, "baseline-str"),
            ("contabil", 1.0, "2026-01-01", None, "baseline-str"),
            ("financeira", 1.0, "2026-01-01", None, "baseline-str"),
            ("operacional", 1.0, "2026-01-01", None, "baseline-str"),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        meta = repo.obter_metadados_macro_validos_na_data(date(2026, 6, 1))
        assert meta[Dimensao.FISCAL].vigencia_inicio == date(2026, 1, 1)
        assert meta[Dimensao.TECNOLOGICA].vigencia_fim == date(2027, 1, 1)
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_dimensao_desconhecida_value_error(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [("slug_inexistente", 1.5, date(2026, 1, 1), None, None)]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        with pytest.raises(ValueError, match="Dimensão desconhecida"):
            repo.obter_pesos_macro_validos_na_data(date(2026, 1, 1))

    @patch(
        "src.infrastructure.repositories.postgres_normativa_score_macro_repository.psycopg2.connect",
    )
    def test_vigencia_inicio_nula_value_error(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("fiscal", 1.5, None, None, "x"),
            ("tecnologica", 1.3, date(2026, 1, 1), None, "x"),
            ("compliance_abnt_17301", 1.2, date(2026, 1, 1), None, "x"),
            ("estrategica", 1.0, date(2026, 1, 1), None, "x"),
            ("contabil", 1.0, date(2026, 1, 1), None, "x"),
            ("financeira", 1.0, date(2026, 1, 1), None, "x"),
            ("operacional", 1.0, date(2026, 1, 1), None, "x"),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaScoreMacroRepository("postgresql://x")
        with pytest.raises(ValueError, match="vigencia_inicio nula"):
            repo.obter_metadados_macro_validos_na_data(date(2026, 1, 1))
