"""Testes de detecção de tabela empresa_painel_arquivo ausente."""

from __future__ import annotations

from src.infrastructure.repositories.postgres_empresa_painel_arquivo_compat import (
    erro_tabela_empresa_painel_arquivo_ausente,
)


class TestPostgresEmpresaPainelArquivoCompat:
    def test_detecta_undefined_table(self) -> None:
        try:
            import psycopg2.errors
        except ImportError:
            return
        exc = psycopg2.errors.UndefinedTable('relation "empresa_painel_arquivo" does not exist')
        assert erro_tabela_empresa_painel_arquivo_ausente(exc) is True

    def test_ignora_outras_tabelas(self) -> None:
        try:
            import psycopg2.errors
        except ImportError:
            return
        exc = psycopg2.errors.UndefinedTable('relation "outra" does not exist')
        assert erro_tabela_empresa_painel_arquivo_ausente(exc) is False
