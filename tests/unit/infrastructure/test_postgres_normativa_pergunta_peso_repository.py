"""Testes unitários do repositório Postgres de overlay de peso por pergunta (sem container)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import psycopg2.errors
import pytest

from src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository import (
    PostgresNormativaPerguntaPesoRepository,
)


class TestPostgresNormativaPerguntaPesoRepository:
    """Mapeia falhas de conexão, migração ausente e parsing de vigência."""

    @patch(
        "src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository.psycopg2.connect",
        side_effect=Exception("offline"),
    )
    def test_conexao_falha_runtime_error(self, _mock_connect: MagicMock) -> None:
        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        with pytest.raises(RuntimeError, match="Falha ao conectar"):
            repo.obter_metadados_por_codigo_validos_na_data(
                date(2026, 5, 9),
                frozenset({"Q-EST-001"}),
            )

    @patch(
        "src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository.psycopg2.connect",
    )
    def test_tabela_ausente_retorna_vazio_sem_excecao(self, mock_connect: MagicMock) -> None:
        """Bases sem migração 0042 — overlay opcional; catálogo JSON continua válido."""
        conn = MagicMock()
        cur = MagicMock()
        cur.execute.side_effect = psycopg2.errors.UndefinedTable("missing")
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        out = repo.obter_metadados_por_codigo_validos_na_data(
            date(2026, 1, 1),
            frozenset({"Q-EST-001"}),
        )
        assert out == {}
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository.psycopg2.connect",
    )
    def test_obter_metadados_retorna_mapa(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("Q-EST-001", 9.0, date(2026, 1, 1), None, "overlay-test"),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        out = repo.obter_metadados_por_codigo_validos_na_data(
            date(2026, 1, 1),
            frozenset({"Q-EST-001"}),
        )
        assert out["Q-EST-001"].peso == 9.0
        assert out["Q-EST-001"].rotulo_versao == "overlay-test"
        conn.close.assert_called_once()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository.psycopg2.connect",
    )
    def test_codigos_vazio_retorna_dict_vazio(self, mock_connect: MagicMock) -> None:
        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        assert repo.obter_metadados_por_codigo_validos_na_data(date(2026, 1, 1), frozenset()) == {}
        mock_connect.assert_not_called()

    @patch(
        "src.infrastructure.repositories.postgres_normativa_pergunta_peso_repository.psycopg2.connect",
    )
    def test_vigencia_inicio_nula_value_error(self, mock_connect: MagicMock) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("Q-X", 1.0, None, None, None),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        with pytest.raises(ValueError, match="vigencia_inicio nula"):
            repo.obter_metadados_por_codigo_validos_na_data(
                date(2026, 1, 1),
                frozenset({"Q-X"}),
            )
        """Alguns drivers devolvem DATE como str — normalizamos para ``date``."""
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = [
            ("Q-FIS-001", 8.0, "2026-01-01", "2026-12-31", None),
        ]
        conn.cursor.return_value.__enter__.return_value = cur
        conn.cursor.return_value.__exit__.return_value = None
        mock_connect.return_value = conn

        repo = PostgresNormativaPerguntaPesoRepository("postgresql://x")
        meta = repo.obter_metadados_por_codigo_validos_na_data(
            date(2026, 6, 1),
            frozenset({"Q-FIS-001"}),
        )
        assert meta["Q-FIS-001"].vigencia_inicio == date(2026, 1, 1)
        assert meta["Q-FIS-001"].vigencia_fim == date(2026, 12, 31)
