"""Testes do GET export-portabilidade (privacidade)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    ResultadoExportPortabilidadeDiagnostico,
)
from src.presentation.api.dependencies import get_gerar_export_portabilidade_diagnostico_use_case
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer

client = TestClient(app)


@pytest.fixture
def _reset_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("_reset_overrides")
def test_export_json_anexo_bytes() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    sid = uuid.uuid4()

    resultado = ResultadoExportPortabilidadeDiagnostico(
        payload={"schema_id": "qdi-diagnostico-export-v1"},
        json_utf8=b'{"schema_id":"qdi-diagnostico-export-v1"}',
        pdf_bytes=None,
    )
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=resultado)

    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc

    r = client.get(
        f"/privacidade/diagnosticos/{did}/export-portabilidade",
        params={"solicitacao_id": str(sid), "formato": "json"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )
    assert r.status_code == 200
    assert "application/json" in r.headers.get("content-type", "")
    assert r.content.startswith(b"{")


@pytest.mark.usefixtures("_reset_overrides")
def test_export_pdf_bytes() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    sid = uuid.uuid4()

    resultado = ResultadoExportPortabilidadeDiagnostico(
        payload={},
        json_utf8=b"{}",
        pdf_bytes=b"%PDF-1.4",
    )
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=resultado)

    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc

    r = client.get(
        f"/privacidade/diagnosticos/{did}/export-portabilidade",
        params={"solicitacao_id": str(sid), "formato": "pacote_pdf"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )
    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/pdf"
    assert r.content.startswith(b"%PDF")


@pytest.mark.usefixtures("_reset_overrides")
def test_export_pdf_sem_bytes_500() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    sid = uuid.uuid4()

    resultado = ResultadoExportPortabilidadeDiagnostico(
        payload={},
        json_utf8=b"{}",
        pdf_bytes=None,
    )
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=resultado)

    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc

    r = client.get(
        f"/privacidade/diagnosticos/{did}/export-portabilidade",
        params={"solicitacao_id": str(sid), "formato": "pacote_pdf"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )
    assert r.status_code == 500


@pytest.mark.usefixtures("_reset_overrides")
def test_export_value_error_400() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    sid = uuid.uuid4()

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(side_effect=ValueError("Solicitação LGPD não encontrada"))

    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc

    r = client.get(
        f"/privacidade/diagnosticos/{did}/export-portabilidade",
        params={"solicitacao_id": str(sid)},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )
    assert r.status_code == 400
