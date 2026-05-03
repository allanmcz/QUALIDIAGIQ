"""Testes do ``PostgresDiagnosticoRepository`` com mock de ``psycopg2.connect``."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)


def _diag_minimo() -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Empresa Teste",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="6201500",
        uf="SP",
        setor_macro=SetorMacro.SERVICOS,
    )
    return Diagnostico(
        tenant_id=uuid4(),
        empresa=emp,
        respondente=Respondente(email="a@b.com", nome="Nome QA"),
        plano=PlanoDiagnostico.GRATUITO,
    )


def _mock_conn_cursor(mock_cursor: MagicMock) -> MagicMock:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_cursor
    mock_cm.__exit__.return_value = None
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cm
    return mock_conn


def _row_minima(did, tid) -> dict:
    return {
        "id": str(did),
        "tenant_id": str(tid),
        "respondente_email": "a@b.com",
        "respondente_nome": "Nome",
        "respondente_cargo": None,
        "respondente_telefone": None,
        "empresa_cnpj": "12345678000195",
        "empresa_razao_social": "Empresa",
        "empresa_porte": "micro",
        "empresa_regime": "simples_nacional",
        "empresa_cnae": "6201500",
        "empresa_uf": "SP",
        "empresa_setor_macro": "servicos",
        "empresa_faixa_faturamento": None,
        "status": "finalizado",
        "plano": "gratuito",
        "score_geral": 50.0,
        "relatorio_pdf_url": None,
        "criado_em": datetime.now(UTC),
        "finalizado_em": datetime.now(UTC),
        "hash_sha256": None,
        "score_completo": None,
        "versao_otimista": 1,
        "checklist_m12_estado": None,
        "quadro_implantacao_anotacoes": None,
        "aceite_termos_privacidade_em": None,
        "locale_relatorio": "pt-BR",
    }


@pytest.mark.asyncio
class TestPostgresDiagnosticoRepository:
    """I/O simulado — sem Postgres real."""

    async def test_salvar_commita(self) -> None:
        mock_cursor = MagicMock()
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.salvar(_diag_minimo())
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    async def test_salvar_rollback_em_erro(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = RuntimeError("db down")
        mock_conn = _mock_conn_cursor(mock_cursor)
        with (
            patch(
                "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
                return_value=mock_conn,
            ),
            pytest.raises(RuntimeError, match="db down"),
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            await repo.salvar(_diag_minimo())
        mock_conn.rollback.assert_called_once()

    async def test_buscar_por_id_retorna_entidade(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _row_minima(did, tid)
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.buscar_por_id(did, tid)
        assert out is not None
        assert out.id == did
        assert out.status == StatusDiagnostico.FINALIZADO

    async def test_buscar_por_id_none(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.buscar_por_id(uuid4(), uuid4())
        assert out is None

    async def test_listar_por_tenant(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [_row_minima(did, tid)]
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            rows = await repo.listar_por_tenant(tid, limit=10, offset=0)
        assert len(rows) == 1
        assert rows[0].id == did

    async def test_atualizar_relatorio_retorna_none_se_zero_linhas(self) -> None:
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_relatorio_pdf_com_versao(
                uuid4(), uuid4(), "https://x/p.pdf", versao_esperada=1
            )
        assert out is None

    async def test_atualizar_relatorio_retorna_entidade(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = _row_minima(did, tid)
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_relatorio_pdf_com_versao(
                did, tid, "https://x/p.pdf", versao_esperada=1
            )
        assert out is not None
        assert out.id == did

    async def test_atualizar_quadro_implantacao(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        row = _row_minima(did, tid)
        row["quadro_implantacao_anotacoes"] = {"f0_a0": {"comentario": "x", "prazo_meta": ""}}
        mock_cursor.fetchone.return_value = row
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_quadro_implantacao_com_versao(
                did, tid, {"f0_a0": {"comentario": "x", "prazo_meta": ""}}, versao_esperada=1
            )
        assert out is not None
        assert out.quadro_implantacao_anotacoes == {"f0_a0": {"comentario": "x", "prazo_meta": ""}}

    async def test_atualizar_m12(self) -> None:
        did, tid = uuid4(), uuid4()
        mock_cursor = MagicMock()
        row = _row_minima(did, tid)
        row["checklist_m12_estado"] = [True] * 10
        mock_cursor.fetchone.return_value = row
        mock_conn = _mock_conn_cursor(mock_cursor)
        with patch(
            "src.infrastructure.repositories.postgres_diagnostico_repository.psycopg2.connect",
            return_value=mock_conn,
        ):
            repo = PostgresDiagnosticoRepository(dsn_sync="postgresql://u:p@localhost:1/db")
            out = await repo.atualizar_checklist_m12_com_versao(
                did, tid, [True] * 10, versao_esperada=1
            )
        assert out is not None
        assert out.checklist_m12_estado == [True] * 10
