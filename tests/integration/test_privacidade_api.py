"""Testes de integração HTTP para /privacidade/solicitacoes."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.errors import (
    EliminacaoDiagnosticoFinalizadoWormError,
    ErroPersistenciaLgpdError,
)
from src.application.ports.lgpd_anonimizacao_executor_port import (
    LgpdAnonimizacaoExecutorPort,
)
from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort
from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ExecutarAnonimizacaoRespondenteLgpd,
)
from src.application.use_cases.executar_eliminacao_diagnostico_lgpd import (
    ExecutarEliminacaoDiagnosticoLgpd,
)
from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    ResultadoExportPortabilidadeDiagnostico,
)
from src.presentation.api.dependencies import (
    get_executar_anonimizacao_respondente_lgpd_use_case,
    get_executar_eliminacao_diagnostico_lgpd_use_case,
    get_gerar_export_portabilidade_diagnostico_use_case,
    get_lgpd_titular_solicitacao_port,
    get_listar_solicitacao_titular_lgpd_use_case,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer


class RecordingEliminacaoExecutor(LgpdEliminacaoExecutorPort):
    """Executor fake para asserts HTTP sem Postgres."""

    def __init__(self, *, raise_worm: bool = False) -> None:
        self.calls: list[tuple[UUID, UUID, UUID, UUID]] = []
        self.raise_worm = raise_worm

    async def aplicar_eliminacao_diagnostico(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        if self.raise_worm:
            raise EliminacaoDiagnosticoFinalizadoWormError(
                "Diagnóstico finalizado: use anonimização."
            )
        self.calls.append((tenant_id, diagnostico_id, solicitacao_id, actor_user_id))


class RecordingAnonimizacaoExecutor(LgpdAnonimizacaoExecutorPort):
    """Executor fake para asserts HTTP sem Postgres."""

    def __init__(self) -> None:
        self.calls: list[tuple[UUID, UUID, UUID, UUID]] = []

    async def aplicar_anonimizacao_respondente(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        self.calls.append((tenant_id, diagnostico_id, solicitacao_id, actor_user_id))


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

    async def buscar_por_id(
        self, *, tenant_id: UUID, solicitacao_id: UUID
    ) -> SolicitacaoTitular | None:
        for row in self.rows:
            if row.id == solicitacao_id and row.tenant_id == tenant_id:
                return row
        return None

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
def privacidade_anonimizar_overrides() -> tuple[FakeLgpdPort, RecordingAnonimizacaoExecutor]:
    fake_port = FakeLgpdPort()
    executor = RecordingAnonimizacaoExecutor()
    app.dependency_overrides[get_lgpd_titular_solicitacao_port] = lambda: fake_port
    app.dependency_overrides[get_executar_anonimizacao_respondente_lgpd_use_case] = (
        lambda: ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=fake_port,
            executor=executor,
        )
    )
    yield fake_port, executor
    app.dependency_overrides = {}


@pytest.fixture
def privacidade_eliminacao_overrides() -> tuple[FakeLgpdPort, RecordingEliminacaoExecutor]:
    fake_port = FakeLgpdPort()
    executor = RecordingEliminacaoExecutor()
    app.dependency_overrides[get_lgpd_titular_solicitacao_port] = lambda: fake_port
    app.dependency_overrides[get_executar_eliminacao_diagnostico_lgpd_use_case] = (
        lambda: ExecutarEliminacaoDiagnosticoLgpd(
            port_solicitacoes=fake_port,
            executor=executor,
        )
    )
    yield fake_port, executor
    app.dependency_overrides = {}


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_get_privacidade_solicitacoes_503_erro_persistencia(
    async_client: AsyncClient,
) -> None:
    """Persistência LGPD falha → 503 JSON (evitar 500 genérico ao browser)."""
    uc = AsyncMock()
    uc.execute.side_effect = ErroPersistenciaLgpdError("Base LGPD indisponível.")

    app.dependency_overrides[get_listar_solicitacao_titular_lgpd_use_case] = lambda: uc
    try:
        headers = cabecalho_auth_bearer(usuario_id=uuid4(), tenant_id=uuid4())
        response = await async_client.get("/privacidade/solicitacoes", headers=headers)
        assert response.status_code == 503
        assert response.json()["detail"] == "Base LGPD indisponível."
    finally:
        app.dependency_overrides.pop(get_listar_solicitacao_titular_lgpd_use_case, None)


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


def _deferida_eliminacao(
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    solicitacao_id: UUID,
    diagnostico_id: UUID,
) -> SolicitacaoTitular:
    now = datetime.now(UTC)
    return SolicitacaoTitular(
        id=solicitacao_id,
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        tipo=TipoSolicitacaoTitular.ELIMINACAO,
        status=StatusSolicitacaoTitular.DEFERIDA,
        canal=CanalSolicitacaoTitular.PLATAFORMA,
        solicitante_email="titular@example.com",
        payload={},
        observacao_interna=None,
        actor_user_id=usuario_id,
        criado_em=now,
        atualizado_em=now,
    )


def _deferida_anonimizacao(
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    solicitacao_id: UUID,
    diagnostico_id: UUID,
) -> SolicitacaoTitular:
    now = datetime.now(UTC)
    return SolicitacaoTitular(
        id=solicitacao_id,
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        tipo=TipoSolicitacaoTitular.ANONIMIZACAO,
        status=StatusSolicitacaoTitular.DEFERIDA,
        canal=CanalSolicitacaoTitular.PLATAFORMA,
        solicitante_email="titular@example.com",
        payload={},
        observacao_interna=None,
        actor_user_id=usuario_id,
        criado_em=now,
        atualizado_em=now,
    )


@pytest.mark.asyncio
async def test_post_anonimizar_respondente_chama_executor(
    async_client,
    privacidade_anonimizar_overrides: tuple[FakeLgpdPort, RecordingAnonimizacaoExecutor],
):
    fake_port, executor = privacidade_anonimizar_overrides
    tenant_id = uuid4()
    usuario_id = uuid4()
    solicitacao_id = uuid4()
    diagnostico_id = uuid4()
    fake_port.rows.append(
        _deferida_anonimizacao(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            solicitacao_id=solicitacao_id,
            diagnostico_id=diagnostico_id,
        )
    )
    headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
    resp = await async_client.post(
        f"/privacidade/diagnosticos/{diagnostico_id}/anonimizar-respondente",
        json={"solicitacao_id": str(solicitacao_id)},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["diagnostico_id"] == str(diagnostico_id)
    assert body["solicitacao_id"] == str(solicitacao_id)
    assert executor.calls == [(tenant_id, diagnostico_id, solicitacao_id, usuario_id)]


@pytest.mark.asyncio
async def test_post_anonimizar_respondente_400_se_nao_deferida(
    async_client,
    privacidade_anonimizar_overrides: tuple[FakeLgpdPort, RecordingAnonimizacaoExecutor],
):
    fake_port, executor = privacidade_anonimizar_overrides
    tenant_id = uuid4()
    usuario_id = uuid4()
    solicitacao_id = uuid4()
    diagnostico_id = uuid4()
    fake_port.rows.append(
        replace(
            _deferida_anonimizacao(
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                solicitacao_id=solicitacao_id,
                diagnostico_id=diagnostico_id,
            ),
            status=StatusSolicitacaoTitular.EM_ANALISE,
        )
    )
    headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
    resp = await async_client.post(
        f"/privacidade/diagnosticos/{diagnostico_id}/anonimizar-respondente",
        json={"solicitacao_id": str(solicitacao_id)},
        headers=headers,
    )
    assert resp.status_code == 400
    assert executor.calls == []


@pytest.mark.asyncio
async def test_post_eliminar_diagnostico_chama_executor(
    async_client,
    privacidade_eliminacao_overrides: tuple[FakeLgpdPort, RecordingEliminacaoExecutor],
):
    fake_port, executor = privacidade_eliminacao_overrides
    tenant_id = uuid4()
    usuario_id = uuid4()
    solicitacao_id = uuid4()
    diagnostico_id = uuid4()
    fake_port.rows.append(
        _deferida_eliminacao(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            solicitacao_id=solicitacao_id,
            diagnostico_id=diagnostico_id,
        )
    )
    headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
    resp = await async_client.post(
        f"/privacidade/diagnosticos/{diagnostico_id}/eliminar-diagnostico",
        json={"solicitacao_id": str(solicitacao_id)},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["diagnostico_id"] == str(diagnostico_id)
    assert body["solicitacao_id"] == str(solicitacao_id)
    assert executor.calls == [(tenant_id, diagnostico_id, solicitacao_id, usuario_id)]


@pytest.mark.asyncio
async def test_post_eliminar_diagnostico_400_quando_tipo_nao_eliminacao(
    async_client,
    privacidade_eliminacao_overrides: tuple[FakeLgpdPort, RecordingEliminacaoExecutor],
):
    """Fluxo técnico de eliminação exige solicitação tipo eliminacao (não anonimizacao)."""
    fake_port, executor = privacidade_eliminacao_overrides
    tenant_id = uuid4()
    usuario_id = uuid4()
    solicitacao_id = uuid4()
    diagnostico_id = uuid4()
    fake_port.rows.append(
        _deferida_anonimizacao(
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            solicitacao_id=solicitacao_id,
            diagnostico_id=diagnostico_id,
        )
    )
    headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
    resp = await async_client.post(
        f"/privacidade/diagnosticos/{diagnostico_id}/eliminar-diagnostico",
        json={"solicitacao_id": str(solicitacao_id)},
        headers=headers,
    )
    assert resp.status_code == 400
    assert "eliminação" in str(resp.json().get("detail", "")).lower()
    assert executor.calls == []


@pytest.mark.asyncio
async def test_post_eliminar_diagnostico_422_quando_worm_finalizado(async_client):
    """Simula adapter Postgres quando diagnóstico já está finalizado — HTTP 422."""
    fake_port = FakeLgpdPort()
    executor = RecordingEliminacaoExecutor(raise_worm=True)
    app.dependency_overrides[get_lgpd_titular_solicitacao_port] = lambda: fake_port
    app.dependency_overrides[get_executar_eliminacao_diagnostico_lgpd_use_case] = (
        lambda: ExecutarEliminacaoDiagnosticoLgpd(
            port_solicitacoes=fake_port,
            executor=executor,
        )
    )
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        solicitacao_id = uuid4()
        diagnostico_id = uuid4()
        fake_port.rows.append(
            _deferida_eliminacao(
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                solicitacao_id=solicitacao_id,
                diagnostico_id=diagnostico_id,
            )
        )
        headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
        resp = await async_client.post(
            f"/privacidade/diagnosticos/{diagnostico_id}/eliminar-diagnostico",
            json={"solicitacao_id": str(solicitacao_id)},
            headers=headers,
        )
        assert resp.status_code == 422
        assert "anonimização" in str(resp.json().get("detail", "")).lower()
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_export_portabilidade_json_200(async_client):
    """GET export JSON — contrato HTTP com use case mockado (integração ASGI)."""
    mock_uc = MagicMock()
    payload_json = b'{"schema_id":"qdi-diagnostico-export-v1"}'
    mock_uc.execute = AsyncMock(
        return_value=ResultadoExportPortabilidadeDiagnostico(
            payload={"schema_id": "qdi-diagnostico-export-v1"},
            json_utf8=payload_json,
            pdf_bytes=None,
        )
    )
    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        diagnostico_id = uuid4()
        solicitacao_id = uuid4()
        headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
        r = await async_client.get(
            f"/privacidade/diagnosticos/{diagnostico_id}/export-portabilidade",
            params={"solicitacao_id": str(solicitacao_id), "formato": "json"},
            headers=headers,
        )
        assert r.status_code == 200
        assert "application/json" in (r.headers.get("content-type") or "")
        assert r.content == payload_json
        mock_uc.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_gerar_export_portabilidade_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_get_export_portabilidade_pacote_pdf_200(async_client):
    """GET export pacote_pdf — PDF binário e comando com gerar_pdf_anexo=True."""
    mock_uc = MagicMock()
    pdf_stub = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    mock_uc.execute = AsyncMock(
        return_value=ResultadoExportPortabilidadeDiagnostico(
            payload={},
            json_utf8=b"{}",
            pdf_bytes=pdf_stub,
        )
    )
    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        diagnostico_id = uuid4()
        solicitacao_id = uuid4()
        headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
        r = await async_client.get(
            f"/privacidade/diagnosticos/{diagnostico_id}/export-portabilidade",
            params={"solicitacao_id": str(solicitacao_id), "formato": "pacote_pdf"},
            headers=headers,
        )
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/pdf"
        assert r.content.startswith(b"%PDF")
        assert r.content == pdf_stub
        mock_uc.execute.assert_awaited_once()
        comando = mock_uc.execute.await_args.args[0]
        assert comando.gerar_pdf_anexo is True
        assert comando.diagnostico_id == diagnostico_id
        assert comando.solicitacao_id == solicitacao_id
        assert comando.tenant_id == tenant_id
    finally:
        app.dependency_overrides.pop(get_gerar_export_portabilidade_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_get_export_portabilidade_pacote_pdf_500_sem_pdf(async_client):
    """pacote_pdf sem pdf_bytes no resultado → 500 (contrato router)."""
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(
        return_value=ResultadoExportPortabilidadeDiagnostico(
            payload={},
            json_utf8=b"{}",
            pdf_bytes=None,
        )
    )
    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        diagnostico_id = uuid4()
        solicitacao_id = uuid4()
        headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
        r = await async_client.get(
            f"/privacidade/diagnosticos/{diagnostico_id}/export-portabilidade",
            params={"solicitacao_id": str(solicitacao_id), "formato": "pacote_pdf"},
            headers=headers,
        )
        assert r.status_code == 500
        assert "PDF" in str(r.json().get("detail", ""))
    finally:
        app.dependency_overrides.pop(get_gerar_export_portabilidade_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_get_export_portabilidade_400_valor_negocio(async_client):
    """Erro de negócio do use case → 400 (ex.: solicitação não deferida)."""
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(side_effect=ValueError("Solicitação deve estar deferida"))
    app.dependency_overrides[get_gerar_export_portabilidade_diagnostico_use_case] = lambda: mock_uc
    try:
        tenant_id = uuid4()
        usuario_id = uuid4()
        diagnostico_id = uuid4()
        solicitacao_id = uuid4()
        headers = cabecalho_auth_bearer(usuario_id=usuario_id, tenant_id=tenant_id)
        r = await async_client.get(
            f"/privacidade/diagnosticos/{diagnostico_id}/export-portabilidade",
            params={"solicitacao_id": str(solicitacao_id)},
            headers=headers,
        )
        assert r.status_code == 400
        assert "deferida" in str(r.json().get("detail", ""))
    finally:
        app.dependency_overrides.pop(get_gerar_export_portabilidade_diagnostico_use_case, None)
