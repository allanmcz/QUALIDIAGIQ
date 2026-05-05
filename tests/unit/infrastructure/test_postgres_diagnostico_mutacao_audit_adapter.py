"""Testes do adapter Postgres de auditoria de mutação pós-finalização."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from psycopg2.extras import Json

from src.application.ports.diagnostico_mutacao_audit_port import TipoMutacaoDiagnostico
from src.infrastructure.adapters.postgres_diagnostico_mutacao_audit_adapter import (
    PostgresDiagnosticoMutacaoAuditAdapter,
)


@pytest.mark.asyncio
async def test_registrar_executa_insert_e_commit() -> None:
    tid = uuid4()
    did = uuid4()
    actor = uuid4()
    cur = MagicMock()
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = None
    conn = MagicMock()
    conn.cursor.return_value = cm
    with patch(
        "src.infrastructure.adapters.postgres_diagnostico_mutacao_audit_adapter.psycopg2.connect",
        return_value=conn,
    ) as m_connect:
        ad = PostgresDiagnosticoMutacaoAuditAdapter("postgresql://u:p@h:5432/db")
        await ad.registrar(
            tenant_id=tid,
            diagnostico_id=did,
            tipo=TipoMutacaoDiagnostico.RELATORIO_PDF,
            payload={"relatorio_pdf_url": "https://x/p.pdf"},
            actor_user_id=actor,
            versao_otimista_antes=3,
            versao_otimista_apos=4,
        )
    m_connect.assert_called_once_with("postgresql://u:p@h:5432/db")
    cur.execute.assert_called_once()
    args, _kwargs = cur.execute.call_args
    assert "INSERT INTO diagnostico_mutacao_audit" in args[0]
    sql_params = args[1]
    assert sql_params[0] is tid
    assert sql_params[1] is did
    assert sql_params[2] == "relatorio_pdf"
    assert isinstance(sql_params[3], Json)
    assert sql_params[4] is actor
    assert sql_params[5] == 3
    assert sql_params[6] == 4
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_registrar_rollback_quando_execute_falha() -> None:
    cur = MagicMock()
    cur.execute.side_effect = RuntimeError("db")
    cm = MagicMock()
    cm.__enter__.return_value = cur
    cm.__exit__.return_value = None
    conn = MagicMock()
    conn.cursor.return_value = cm
    with patch(
        "src.infrastructure.adapters.postgres_diagnostico_mutacao_audit_adapter.psycopg2.connect",
        return_value=conn,
    ):
        ad = PostgresDiagnosticoMutacaoAuditAdapter("postgresql://u:p@h:5432/db")
        with pytest.raises(RuntimeError, match="db"):
            await ad.registrar(
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                tipo=TipoMutacaoDiagnostico.M12_LIKERT,
                payload={"checklist_m12_estado": [1] * 10},
                actor_user_id=None,
                versao_otimista_antes=1,
                versao_otimista_apos=2,
            )
    conn.rollback.assert_called_once()
    conn.close.assert_called_once()
