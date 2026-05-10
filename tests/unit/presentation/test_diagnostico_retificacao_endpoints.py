"""Testes HTTP de retificação (router core)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.presentation.api.dependencies import (
    get_listar_retificacoes_diagnostico_use_case,
    get_registrar_retificacao_diagnostico_use_case,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer

client = TestClient(app)


@pytest.fixture
def _reset_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("_reset_overrides")
def test_post_retificacao_201() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    reg_id = uuid.uuid4()
    reg = DiagnosticoRetificacaoRegisto(
        id=reg_id,
        tenant_id=tid,
        diagnostico_original_id=did,
        hash_diagnostico_original_sha256="aa" * 32,
        motivo_retificacao="Correção após revisão documental",
        payload_retificacao={},
        hash_retificacao_sha256="bb" * 32,
        actor_user_id=uid,
        criado_em=datetime.now(UTC),
    )
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=reg)

    app.dependency_overrides[get_registrar_retificacao_diagnostico_use_case] = lambda: mock_uc

    r = client.post(
        f"/diagnosticos/{did}/retificacao",
        json={
            "motivo_retificacao": "Correção após revisão documental",
            "payload_retificacao": {},
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert r.status_code == 201
    assert r.json()["id"] == str(reg_id)


@pytest.mark.usefixtures("_reset_overrides")
def test_post_retificacao_400_value_error() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(side_effect=ValueError("Diagnóstico não encontrado."))

    app.dependency_overrides[get_registrar_retificacao_diagnostico_use_case] = lambda: mock_uc

    r = client.post(
        f"/diagnosticos/{did}/retificacao",
        json={
            "motivo_retificacao": "Correção após revisão documental",
            "payload_retificacao": {},
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert r.status_code == 400


@pytest.mark.usefixtures("_reset_overrides")
def test_get_retificacoes_lista() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    did = uuid.uuid4()
    reg = DiagnosticoRetificacaoRegisto(
        id=uuid.uuid4(),
        tenant_id=tid,
        diagnostico_original_id=did,
        hash_diagnostico_original_sha256="aa" * 32,
        motivo_retificacao="Correção após revisão documental",
        payload_retificacao={},
        hash_retificacao_sha256="bb" * 32,
        actor_user_id=uid,
        criado_em=datetime.now(UTC),
    )
    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=[reg])

    app.dependency_overrides[get_listar_retificacoes_diagnostico_use_case] = lambda: mock_uc

    r = client.get(
        f"/diagnosticos/{did}/retificacoes",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["motivo_retificacao"] == reg.motivo_retificacao
