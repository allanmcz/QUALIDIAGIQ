"""Testes unitários — ``PostgresCnaeSubclasseRepository`` (asyncpg mockado)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import asyncpg.exceptions
import pytest

from src.infrastructure.repositories.postgres_cnae_subclasse_repository import (
    PostgresCnaeSubclasseRepository,
    _escape_like,
)


class TestEscapeLike:
    """Caracteres especiais em ILIKE — ``ESCAPE '\\'``."""

    def test_escapa_metacaracteres(self) -> None:
        assert _escape_like(r"a%b_c\d") == r"a\%b\_c\\d"


class TestPostgresCnaeSubclasseRepositoryInit:
    """Normalização do DSN para asyncpg."""

    def test_dsn_asyncpg_para_postgresql(self) -> None:
        repo = PostgresCnaeSubclasseRepository("postgresql+asyncpg://user:pw@host:5432/db")
        assert repo._dsn == "postgresql://user:pw@host:5432/db"

    def test_dsn_postgresql_mantido(self) -> None:
        repo = PostgresCnaeSubclasseRepository("postgresql://localhost/db")
        assert repo._dsn == "postgresql://localhost/db"


@pytest.mark.asyncio
async def test_buscar_sucesso_mapeia_linhas() -> None:
    rows = [
        {"sid": "4711302", "dsc": "Comércio varejista"},
    ]
    conn = MagicMock()
    conn.fetch = AsyncMock(return_value=rows)
    conn.close = AsyncMock()

    with patch(
        "src.infrastructure.repositories.postgres_cnae_subclasse_repository.asyncpg.connect",
        new_callable=AsyncMock,
        return_value=conn,
    ):
        repo = PostgresCnaeSubclasseRepository("postgresql://x/db")
        out = await repo.buscar(consulta="varejo", limite=15)

    assert len(out) == 1
    assert out[0].subclasse_id == "4711302"
    assert out[0].descricao == "Comércio varejista"
    conn.fetch.assert_awaited_once()
    call_args = conn.fetch.await_args
    sql = call_args[0][0]
    assert "qdi.cnae_subclasse" in sql
    assert call_args[0][1:]  # args posicionais (LIKE + limite)
    conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_buscar_consulta_so_digitos_inclui_prefixo_subclasse() -> None:
    conn = MagicMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.close = AsyncMock()

    with patch(
        "src.infrastructure.repositories.postgres_cnae_subclasse_repository.asyncpg.connect",
        new_callable=AsyncMock,
        return_value=conn,
    ):
        repo = PostgresCnaeSubclasseRepository("postgresql://x/db")
        await repo.buscar(consulta="4711302", limite=10)

    args = conn.fetch.await_args[0]
    assert "subclasse_id::text LIKE $1" in args[0]


@pytest.mark.asyncio
async def test_buscar_conexao_falha_runtime_error() -> None:
    with patch(
        "src.infrastructure.repositories.postgres_cnae_subclasse_repository.asyncpg.connect",
        new_callable=AsyncMock,
        side_effect=ConnectionError("recusado"),
    ):
        repo = PostgresCnaeSubclasseRepository("postgresql://x/db")
        with pytest.raises(RuntimeError, match="conectar ao Postgres"):
            await repo.buscar(consulta="x", limite=5)


@pytest.mark.asyncio
async def test_buscar_tabela_ausente_runtime_error() -> None:
    conn = MagicMock()
    conn.fetch = AsyncMock(side_effect=asyncpg.exceptions.UndefinedTableError("relation"))
    conn.close = AsyncMock()

    with patch(
        "src.infrastructure.repositories.postgres_cnae_subclasse_repository.asyncpg.connect",
        new_callable=AsyncMock,
        return_value=conn,
    ):
        repo = PostgresCnaeSubclasseRepository("postgresql://x/db")
        with pytest.raises(RuntimeError, match=r"Tabela qdi\.cnae_subclasse"):
            await repo.buscar(consulta="texto", limite=5)

    conn.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_buscar_linha_invalida_ignora_sem_interromper() -> None:
    rows = [
        {"sid": "99999999", "dsc": "sid com 8 dígitos — ValueError"},
        {"sid": "1234567", "dsc": "OK"},
    ]
    conn = MagicMock()
    conn.fetch = AsyncMock(return_value=rows)
    conn.close = AsyncMock()

    with patch(
        "src.infrastructure.repositories.postgres_cnae_subclasse_repository.asyncpg.connect",
        new_callable=AsyncMock,
        return_value=conn,
    ):
        repo = PostgresCnaeSubclasseRepository("postgresql://x/db")
        out = await repo.buscar(consulta="mix", limite=20)

    assert len(out) == 1
    assert out[0].subclasse_id == "1234567"
