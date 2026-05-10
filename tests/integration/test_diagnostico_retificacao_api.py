"""Integração HTTP — retificações append-only (ADR-012 §5)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.presentation.api.dependencies import (
    get_listar_retificacoes_diagnostico_use_case,
    get_registrar_retificacao_diagnostico_use_case,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_get_retificacoes_lista_vazia_200(async_client):
    """Lista sem linhas — 200 e JSON []."""
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(return_value=[])
    app.dependency_overrides[get_listar_retificacoes_diagnostico_use_case] = lambda: mock_uc
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        diagnostico_id = uuid4()
        r = await async_client.get(
            f"/diagnosticos/{diagnostico_id}/retificacoes",
            headers=cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id),
        )
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.pop(get_listar_retificacoes_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_post_retificacao_201_com_idempotency_key(async_client):
    """POST append-only exige Idempotency-Key no middleware + 201."""
    tenant_id = uuid4()
    usuario_id = uuid4()
    diagnostico_id = uuid4()
    retificacao_id = uuid4()
    agora = datetime.now(UTC)
    reg = DiagnosticoRetificacaoRegisto(
        id=retificacao_id,
        tenant_id=tenant_id,
        diagnostico_original_id=diagnostico_id,
        hash_diagnostico_original_sha256="aa" * 32,
        motivo_retificacao="Correção documental após revisão interna.",
        payload_retificacao={},
        hash_retificacao_sha256="bb" * 32,
        actor_user_id=usuario_id,
        criado_em=agora,
    )
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(return_value=reg)
    app.dependency_overrides[get_registrar_retificacao_diagnostico_use_case] = lambda: mock_uc
    try:
        r = await async_client.post(
            f"/diagnosticos/{diagnostico_id}/retificacao",
            json={
                "motivo_retificacao": "Correção documental após revisão interna.",
                "payload_retificacao": {},
            },
            headers={
                **cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id),
                "Idempotency-Key": str(uuid4()),
            },
        )
        assert r.status_code == 201
        body = r.json()
        assert body["id"] == str(retificacao_id)
        assert body["motivo_retificacao"] == reg.motivo_retificacao
        mock_uc.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_registrar_retificacao_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_post_retificacao_sem_idempotency_key_400(async_client):
    """Middleware — POST retificação sem chave → 400."""
    tenant_id = uuid4()
    usuario_id = uuid4()
    diagnostico_id = uuid4()
    r = await async_client.post(
        f"/diagnosticos/{diagnostico_id}/retificacao",
        json={
            "motivo_retificacao": "Correção documental após revisão interna.",
            "payload_retificacao": {},
        },
        headers=cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id),
    )
    assert r.status_code == 400
    assert "Idempotency" in str(r.json().get("detail", ""))
