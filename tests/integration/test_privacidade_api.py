"""Testes de integração HTTP para /privacidade/solicitacoes."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.presentation.api.dependencies import get_lgpd_titular_solicitacao_port
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer


class FakeLgpdPort(LgpdTitularSolicitacaoPort):
    """Port fake em memória para isolar comportamento HTTP dos endpoints."""

    def __init__(self) -> None:
        self.rows: list[SolicitacaoTitular] = []

    async def criar(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID | None,
        tipo: TipoSolicitacaoTitular,
        canal: CanalSolicitacaoTitular,
        solicitante_email: str,
        payload: dict[str, Any],
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular:
        now = datetime.now(UTC)
        row = SolicitacaoTitular(
            id=uuid4(),
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            tipo=tipo,
            status=StatusSolicitacaoTitular.RECEBIDA,
            canal=canal,
            solicitante_email=solicitante_email,
            payload=payload,
            observacao_interna=None,
            actor_user_id=actor_user_id,
            criado_em=now,
            atualizado_em=now,
        )
        self.rows.append(row)
        return row

    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        status: StatusSolicitacaoTitular | None,
        limit: int,
    ) -> list[SolicitacaoTitular]:
        selected = [r for r in self.rows if r.tenant_id == tenant_id]
        if status is not None:
            selected = [r for r in selected if r.status == status]
        return selected[:limit]

    async def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
        status: StatusSolicitacaoTitular,
        observacao_interna: str | None,
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular | None:
        for idx, row in enumerate(self.rows):
            if row.id == solicitacao_id and row.tenant_id == tenant_id:
                updated = replace(
                    row,
                    status=status,
                    observacao_interna=observacao_interna,
                    actor_user_id=actor_user_id,
                    atualizado_em=datetime.now(UTC),
                )
                self.rows[idx] = updated
                return updated
        return None


@pytest.fixture
def privacidade_overrides() -> FakeLgpdPort:
    fake = FakeLgpdPort()
    app.dependency_overrides[get_lgpd_titular_solicitacao_port] = lambda: fake
    yield fake
    app.dependency_overrides = {}


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_post_privacidade_solicitacao_201(async_client, privacidade_overrides: FakeLgpdPort):
    headers = {
        **cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    payload = {
        "tipo": "acesso",
        "canal": "plataforma",
        "solicitante_email": "titular@example.com",
        "payload": {"motivo": "validacao"},
    }
    response = await async_client.post("/privacidade/solicitacoes", json=payload, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["tipo"] == "acesso"
    assert body["status"] == "recebida"
    assert body["canal"] == "plataforma"
    assert body["solicitante_email"] == "titular@example.com"
    assert len(privacidade_overrides.rows) == 1


@pytest.mark.asyncio
async def test_get_privacidade_solicitacoes_filtro_status(
    async_client, privacidade_overrides: FakeLgpdPort
):
    tenant_id = uuid4()
    user_id = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=user_id, tenant_id=tenant_id)
    other_headers = cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4())

    await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "portabilidade",
            "canal": "self_service",
            "solicitante_email": "a@empresa.com",
            "payload": {},
        },
        headers={**headers, "Idempotency-Key": str(uuid4())},
    )
    second = await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "correcao",
            "canal": "plataforma",
            "solicitante_email": "a@empresa.com",
            "payload": {},
        },
        headers={**headers, "Idempotency-Key": str(uuid4())},
    )
    await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "acesso",
            "canal": "plataforma",
            "solicitante_email": "outro@empresa.com",
            "payload": {},
        },
        headers={**other_headers, "Idempotency-Key": str(uuid4())},
    )

    solic_id = second.json()["id"]
    patch = await async_client.patch(
        f"/privacidade/solicitacoes/{solic_id}/status",
        json={"status": "em_analise", "observacao_interna": "triagem"},
        headers=headers,
    )
    assert patch.status_code == 200

    filtered = await async_client.get(
        "/privacidade/solicitacoes?status=em_analise", headers=headers
    )
    assert filtered.status_code == 200
    rows = filtered.json()
    assert len(rows) == 1
    assert rows[0]["id"] == solic_id
    assert rows[0]["status"] == "em_analise"


@pytest.mark.asyncio
async def test_patch_privacidade_404_quando_nao_encontra(
    async_client, privacidade_overrides: FakeLgpdPort
):
    del privacidade_overrides
    headers = cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4())
    response = await async_client.patch(
        f"/privacidade/solicitacoes/{uuid4()}/status",
        json={"status": "indeferida", "observacao_interna": "sem vinculo"},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_post_privacidade_400_tipo_invalido(
    async_client, privacidade_overrides: FakeLgpdPort
):
    del privacidade_overrides
    headers = {
        **cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    response = await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "inventado",
            "canal": "plataforma",
            "solicitante_email": "x@empresa.com",
            "payload": {},
        },
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_post_privacidade_400_canal_invalido(
    async_client, privacidade_overrides: FakeLgpdPort
):
    del privacidade_overrides
    headers = {
        **cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    response = await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "acesso",
            "canal": "telefone",
            "solicitante_email": "x@empresa.com",
            "payload": {},
        },
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_patch_privacidade_400_status_invalido(
    async_client, privacidade_overrides: FakeLgpdPort
):
    headers = {
        **cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4()),
        "Idempotency-Key": str(uuid4()),
    }
    created = await async_client.post(
        "/privacidade/solicitacoes",
        json={
            "tipo": "acesso",
            "canal": "plataforma",
            "solicitante_email": "x@empresa.com",
            "payload": {},
        },
        headers=headers,
    )
    assert created.status_code == 201
    solic_id = created.json()["id"]

    response = await async_client.patch(
        f"/privacidade/solicitacoes/{solic_id}/status",
        json={"status": "encerrado"},
        headers=headers,
    )
    assert response.status_code == 400
