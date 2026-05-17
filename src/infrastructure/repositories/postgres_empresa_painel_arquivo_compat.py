"""
Compatibilidade quando a migration 0053 ainda não foi aplicada no Postgres.

Camada: Infrastructure
"""

from __future__ import annotations


def erro_tabela_empresa_painel_arquivo_ausente(exc: BaseException) -> bool:
    """True se o erro indica ausência da tabela ``empresa_painel_arquivo``."""
    try:
        import psycopg2.errors
    except ImportError:
        return False
    if not isinstance(exc, psycopg2.errors.UndefinedTable):
        return False
    return "empresa_painel_arquivo" in str(exc)
