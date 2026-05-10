"""Testes unitários dos adapters LGPD Postgres (psycopg2 mockado — sem container)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.application.errors import EliminacaoDiagnosticoFinalizadoWormError
from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter import (
    PostgresLgpdAnonimizacaoExecutorAdapter,
    _aplicar_sync,
)
from src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter import (
    PostgresLgpdEliminacaoExecutorAdapter,
)
from src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter import (
    _aplicar_sync as _aplicar_eliminacao_sync,
)
from src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter import (
    PostgresLgpdTitularSolicitacaoAdapter,
    _atualizar_status_sync,
    _buscar_sync,
    _criar_sync,
    _listar_sync,
)


def _row_solicitacao() -> dict:
    sid, tid = uuid4(), uuid4()
    agora = datetime(2026, 3, 1, 15, 0, tzinfo=UTC)
    return {
        "id": sid,
        "tenant_id": tid,
        "diagnostico_id": None,
        "tipo": "acesso",
        "status": "recebida",
        "canal": "plataforma",
        "solicitante_email": "titular@exemplo.com",
        "payload": {"k": 1},
        "observacao_interna": None,
        "actor_user_id": None,
        "criado_em": agora,
        "atualizado_em": agora,
    }


def _conn_com_cursor(cur: MagicMock) -> MagicMock:
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None
    return conn


class TestPostgresLgpdTitularSolicitacaoSync:
    """Funções síncronas expostas para validação direta (sem thread pool)."""

    def test_buscar_sync_none_quando_sem_linha(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = _conn_com_cursor(cur)
        tid, sid = uuid4(), uuid4()
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            assert _buscar_sync("postgresql://x", tenant_id=tid, solicitacao_id=sid) is None

    def test_buscar_sync_retorna_entidade(self) -> None:
        row = _row_solicitacao()
        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _buscar_sync(
                "postgresql://x",
                tenant_id=row["tenant_id"],
                solicitacao_id=row["id"],
            )
        assert out is not None
        assert out.solicitante_email == "titular@exemplo.com"
        assert out.payload == {"k": 1}

    def test_buscar_from_row_payload_none_vira_dict_vazio(self) -> None:
        row = _row_solicitacao()
        row["payload"] = None
        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _buscar_sync(
                "postgresql://x",
                tenant_id=row["tenant_id"],
                solicitacao_id=row["id"],
            )
        assert out is not None
        assert out.payload == {}

    def test_criar_sync_sucesso(self) -> None:
        row = _row_solicitacao()
        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        tid = row["tenant_id"]
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _criar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=None,
                tipo="acesso",
                canal="plataforma",
                solicitante_email="a@b.com",
                payload={"p": 2},
                actor_user_id=None,
            )
        assert out.tipo == TipoSolicitacaoTitular.ACESSO
        conn.commit.assert_called_once()

    def test_criar_sync_runtime_error_quando_fetchone_vazio(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = _conn_com_cursor(cur)
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="retorno vazio"),
        ):
            _criar_sync(
                "postgresql://x",
                tenant_id=uuid4(),
                diagnostico_id=None,
                tipo="acesso",
                canal="plataforma",
                solicitante_email="a@b.com",
                payload={},
                actor_user_id=None,
            )
        conn.rollback.assert_called_once()

    def test_criar_sync_rollback_quando_execute_falha(self) -> None:
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("sql")
        conn = _conn_com_cursor(cur)
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="sql"),
        ):
            _criar_sync(
                "postgresql://x",
                tenant_id=uuid4(),
                diagnostico_id=None,
                tipo="acesso",
                canal="plataforma",
                solicitante_email="a@b.com",
                payload={},
                actor_user_id=None,
            )
        conn.rollback.assert_called_once()

    def test_listar_sync_sem_filtro_status(self) -> None:
        row = _row_solicitacao()
        cur = MagicMock()
        cur.fetchall.return_value = [row]
        conn = _conn_com_cursor(cur)
        tid = row["tenant_id"]
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _listar_sync("postgresql://x", tenant_id=tid, status=None, limit=10)
        assert len(out) == 1
        sql = cur.execute.call_args[0][0]
        assert "AND status = %s" not in sql

    def test_listar_sync_com_status(self) -> None:
        row = _row_solicitacao()
        cur = MagicMock()
        cur.fetchall.return_value = [row]
        conn = _conn_com_cursor(cur)
        tid = row["tenant_id"]
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _listar_sync("postgresql://x", tenant_id=tid, status="recebida", limit=5)
        assert len(out) == 1
        assert "AND status = %s" in cur.execute.call_args[0][0]

    def test_atualizar_status_sync_none_quando_sem_linha(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = _conn_com_cursor(cur)
        tid, sid = uuid4(), uuid4()
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            assert (
                _atualizar_status_sync(
                    "postgresql://x",
                    tenant_id=tid,
                    solicitacao_id=sid,
                    status="deferida",
                    observacao_interna=None,
                    actor_user_id=None,
                )
                is None
            )

    def test_atualizar_status_sync_sucesso(self) -> None:
        row = _row_solicitacao()
        row["status"] = "deferida"
        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
            return_value=conn,
        ):
            out = _atualizar_status_sync(
                "postgresql://x",
                tenant_id=row["tenant_id"],
                solicitacao_id=row["id"],
                status="deferida",
                observacao_interna="ok",
                actor_user_id=uuid4(),
            )
        assert out is not None
        assert out.status == StatusSolicitacaoTitular.DEFERIDA

    def test_atualizar_status_sync_rollback_em_erro(self) -> None:
        cur = MagicMock()
        cur.execute.side_effect = OSError("io")
        conn = _conn_com_cursor(cur)
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(OSError, match="io"),
        ):
            _atualizar_status_sync(
                "postgresql://x",
                tenant_id=uuid4(),
                solicitacao_id=uuid4(),
                status="deferida",
                observacao_interna=None,
                actor_user_id=None,
            )
        conn.rollback.assert_called_once()


@pytest.mark.asyncio
class TestPostgresLgpdTitularSolicitacaoAdapterAsync:
    """Delegação ``asyncio.to_thread`` para funções síncronas."""

    async def test_adapter_buscar_por_id_via_to_thread(self) -> None:
        row = _row_solicitacao()

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        adapter = PostgresLgpdTitularSolicitacaoAdapter("postgresql://lgpd")

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ),
        ):
            out = await adapter.buscar_por_id(tenant_id=row["tenant_id"], solicitacao_id=row["id"])
        assert out is not None
        assert out.id == row["id"]

    async def test_adapter_criar_via_to_thread(self) -> None:
        row = _row_solicitacao()

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        adapter = PostgresLgpdTitularSolicitacaoAdapter("postgresql://lgpd")

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ),
        ):
            out = await adapter.criar(
                tenant_id=row["tenant_id"],
                diagnostico_id=None,
                tipo=TipoSolicitacaoTitular.ACESSO,
                canal=CanalSolicitacaoTitular.PLATAFORMA,
                solicitante_email="novo@z.com",
                payload={"a": 1},
                actor_user_id=None,
            )
        assert out.solicitante_email == "titular@exemplo.com"

    async def test_adapter_atualizar_status_via_to_thread(self) -> None:
        row = _row_solicitacao()
        row["status"] = "deferida"

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        cur = MagicMock()
        cur.fetchone.return_value = row
        conn = _conn_com_cursor(cur)
        adapter = PostgresLgpdTitularSolicitacaoAdapter("postgresql://lgpd")

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ),
        ):
            out = await adapter.atualizar_status(
                tenant_id=row["tenant_id"],
                solicitacao_id=row["id"],
                status=StatusSolicitacaoTitular.DEFERIDA,
                observacao_interna="ok",
                actor_user_id=uuid4(),
            )
        assert out is not None
        assert out.status == StatusSolicitacaoTitular.DEFERIDA

    async def test_adapter_listar_com_status_via_to_thread(self) -> None:
        row = _row_solicitacao()

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        adapter = PostgresLgpdTitularSolicitacaoAdapter("postgresql://lgpd")
        cur = MagicMock()
        cur.fetchall.return_value = [row]
        conn = _conn_com_cursor(cur)

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.psycopg2.connect",
                return_value=conn,
            ),
            patch(
                "src.infrastructure.adapters.postgres_lgpd_titular_solicitacao_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ),
        ):
            lst = await adapter.listar_por_tenant(
                tenant_id=row["tenant_id"],
                status=StatusSolicitacaoTitular.RECEBIDA,
                limit=5,
            )
        assert len(lst) == 1
        assert lst[0].canal == CanalSolicitacaoTitular.PLATAFORMA


class TestPostgresLgpdAnonimizacaoExecutorSync:
    """Caminhos de ``_aplicar_sync`` (transação única)."""

    def test_aplicar_sync_diagnostico_inexistente(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="não encontrado"),
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )

    def test_aplicar_sync_rejeita_nao_finalizado(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = {"status": "em_andamento"}
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="finalizado"),
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )

    def test_aplicar_sync_sucesso(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "finalizado"}
            elif (
                "UPDATE diagnosticos" in q and "respondente_email" in q
            ) or "UPDATE lgpd_titular_solicitacao" in q:
                cur.rowcount = 1

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
            return_value=conn,
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.commit.assert_called_once()

    def test_aplicar_sync_runtime_error_rowcount_diagnostico(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "finalizado"}
            elif "UPDATE diagnosticos" in q and "respondente_email" in q:
                cur.rowcount = 0

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="rowcount"),
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()

    def test_aplicar_sync_value_error_rowcount_solicitacao(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "finalizado"}
            elif "UPDATE diagnosticos" in q and "respondente_email" in q:
                cur.rowcount = 1
            elif "UPDATE lgpd_titular_solicitacao" in q:
                cur.rowcount = 0

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="deferida"),
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()

    def test_aplicar_sync_rollback_em_erro_generica(self) -> None:
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("db")
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="db"),
        ):
            _aplicar_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()


@pytest.mark.asyncio
class TestPostgresLgpdAnonimizacaoExecutorAdapterAsync:
    async def test_adapter_delega_to_thread(self) -> None:
        adapter = PostgresLgpdAnonimizacaoExecutorAdapter("postgresql://anon")

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ) as tt,
            patch(
                "src.infrastructure.adapters.postgres_lgpd_anonimizacao_executor_adapter._aplicar_sync",
                return_value=None,
            ) as aplicar_mock,
        ):
            await adapter.aplicar_anonimizacao_respondente(
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                solicitacao_id=uuid4(),
                actor_user_id=uuid4(),
            )
        tt.assert_called_once()
        aplicar_mock.assert_called_once()


class TestPostgresLgpdEliminacaoExecutorSync:
    """Caminhos de ``_aplicar_eliminacao_sync`` (DELETE + UPDATE solicitação)."""

    def test_eliminacao_diagnostico_inexistente(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="não encontrado"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )

    def test_eliminacao_rejeita_finalizado_worm(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = {"status": "finalizado"}
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(EliminacaoDiagnosticoFinalizadoWormError, match="anonimização"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )

    def test_eliminacao_rejeita_status_desconhecido(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = {"status": "inventado"}
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="Eliminação física não suportada"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )

    def test_eliminacao_sucesso(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "em_andamento"}
            elif "DELETE FROM diagnosticos" in q or "UPDATE lgpd_titular_solicitacao" in q:
                cur.rowcount = 1

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with patch(
            "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
            return_value=conn,
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.commit.assert_called_once()

    def test_eliminacao_runtime_rowcount_delete(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "cancelado"}
            elif "DELETE FROM diagnosticos" in q:
                cur.rowcount = 0

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="rowcount"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()

    def test_eliminacao_value_error_rowcount_solicitacao(self) -> None:
        cur = MagicMock()

        def execute_side_effect(query: str, params: object | None = None) -> None:
            q = query.replace("\n", " ")
            if "SELECT status" in q and "FROM diagnosticos" in q:
                cur.fetchone.return_value = {"status": "expirado"}
            elif "DELETE FROM diagnosticos" in q:
                cur.rowcount = 1
            elif "UPDATE lgpd_titular_solicitacao" in q:
                cur.rowcount = 0

        cur.execute.side_effect = execute_side_effect
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(ValueError, match="deferida"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()

    def test_eliminacao_rollback_em_erro_generica(self) -> None:
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("db")
        conn = _conn_com_cursor(cur)
        tid, did, sid, actor = uuid4(), uuid4(), uuid4(), uuid4()
        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.psycopg2.connect",
                return_value=conn,
            ),
            pytest.raises(RuntimeError, match="db"),
        ):
            _aplicar_eliminacao_sync(
                "postgresql://x",
                tenant_id=tid,
                diagnostico_id=did,
                solicitacao_id=sid,
                actor_user_id=actor,
            )
        conn.rollback.assert_called_once()


@pytest.mark.asyncio
class TestPostgresLgpdEliminacaoExecutorAdapterAsync:
    async def test_adapter_delega_to_thread(self) -> None:
        adapter = PostgresLgpdEliminacaoExecutorAdapter("postgresql://elim")

        async def run_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
            return fn(*args, **kwargs)

        with (
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter.asyncio.to_thread",
                side_effect=run_imediato,
            ) as tt,
            patch(
                "src.infrastructure.adapters.postgres_lgpd_eliminacao_executor_adapter._aplicar_sync",
                return_value=None,
            ) as aplicar_mock,
        ):
            await adapter.aplicar_eliminacao_diagnostico(
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                solicitacao_id=uuid4(),
                actor_user_id=uuid4(),
            )
        tt.assert_called_once()
        aplicar_mock.assert_called_once()
