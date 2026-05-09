"""Testes HTTP dos endpoints de rascunho self-service (mocks de Postgres via asyncio.to_thread)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import psycopg2
import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_email_service,
    get_realizar_diagnostico_use_case,
    get_self_service_diagnostico_claims,
    get_vincular_diagnosticos_lead_self_service_use_case,
)
from src.presentation.api.main import app
from src.presentation.api.routers import diagnostico_helpers as dh
from src.presentation.api.routers import diagnostico_self_service_router as dss
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
)
from tests.conftest import (
    cabecalho_auth_bearer,
    cabecalho_post_diagnostico,
    cabecalho_post_diagnostico_self_service,
)

PAYLOAD_MIN = {
    "empresa": {
        "cnpj": "12345678000195",
        "razao_social": "ACME Rascunho LTDA",
        "porte": "medio",
        "regime": "lucro_real",
        "cnae_principal": "1234567",
        "uf": "SP",
        "setor_macro": "industria",
    },
    "respondente": {"email": "rascunho-endpoint@example.com", "nome": "Tester"},
    "respostas": [
        {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4},
        {"pergunta_id": "5bd89013-2b3f-5c73-8a73-9351e114f14c", "valor": 3},
    ],
    "aceite_termos_privacidade": True,
}


@pytest.fixture(autouse=True)
def _limpar_codigo_store() -> None:
    codigo_store.limpar_para_testes()
    yield
    codigo_store.limpar_para_testes()


@pytest.fixture
async def rascunho_async_client() -> AsyncClient:
    mock_email = AsyncMock()
    mock_email.enviar_codigo_verificacao_email.return_value = True
    app.dependency_overrides[get_email_service] = lambda: mock_email
    # Evita instanciar cliente Supabase ao resolver POST /rascunho-self-service/concluir (Depends).
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: AsyncMock()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_email_service, None)
    app.dependency_overrides.pop(get_realizar_diagnostico_use_case, None)


@pytest.mark.asyncio
async def test_post_rascunho_sem_dsn_503(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = None
        self_service_tenant_id = uuid4()

    with patch.object(dss, "get_settings", return_value=S()):
        r = await rascunho_async_client.post(
            "/diagnosticos/rascunho-self-service",
            json=PAYLOAD_MIN,
            headers={"Idempotency-Key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
        )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_rascunho_201(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()
        app_env = "test"

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "inserir_rascunho_sync":
            return ("resgate-token-fixo", datetime.now(UTC))
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.post(
                "/diagnosticos/rascunho-self-service",
                json=PAYLOAD_MIN,
                headers={"Idempotency-Key": "b2c3d4e5-f6a7-8901-bcde-f12345678901"},
            )
    assert r.status_code == 201
    body = r.json()
    assert body["resgate_token"] == "resgate-token-fixo"
    assert "mensagem" in body


@pytest.mark.asyncio
async def test_get_resumo_404(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return None
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "invalido"},
            )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_resumo_200(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"

    exp = datetime.now(UTC) + timedelta(hours=12)
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "lead@example.com",
        "payload_json": {"empresa": {"razao_social": "Empresa Resumo SA"}},
        "expira_em": exp,
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "qualquer"},
            )
    assert r.status_code == 200
    body = r.json()
    assert body["empresa_razao_social"] == "Empresa Resumo SA"
    assert body["respondente_email"] == "lead@example.com"


@pytest.mark.asyncio
async def test_get_resumo_empresa_nao_dict_usa_fallback_razao(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    exp = datetime.now(UTC) + timedelta(hours=1)
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "z@z.com",
        "payload_json": {"empresa": "invalido"},
        "expira_em": exp,
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "t" * 24},
            )
    assert r.status_code == 200
    assert r.json()["empresa_razao_social"] == "(sem razão social)"


@pytest.mark.asyncio
async def test_get_resumo_payload_json_como_string_200(rascunho_async_client: AsyncClient) -> None:
    """Alguns drivers devolvem jsonb como str — o handler deve fazer parse."""
    import json

    class S:
        sync_database_url = "postgresql://x"

    exp = datetime.now(UTC) + timedelta(hours=1)
    payload = {"empresa": {"razao_social": "JSON str SA"}, "respondente": {"email": "x@y.com"}}
    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "x@y.com",
        "payload_json": json.dumps(payload),
        "expira_em": exp,
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "t" * 24},
            )
    assert r.status_code == 200
    assert r.json()["empresa_razao_social"] == "JSON str SA"


@pytest.mark.asyncio
async def test_get_resumo_sem_expira_em_404(rascunho_async_client: AsyncClient) -> None:
    """Linha sem ``expira_em`` (corrupta): não expõe metadados — 404 como rascunho inválido."""

    class S:
        sync_database_url = "postgresql://x"

    row = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": "w@w.com",
        "payload_json": {"empresa": {"razao_social": "OK"}},
        "expira_em": None,
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "u" * 24},
            )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_post_concluir_rascunho_201(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            return row
        if n == "marcar_rascunho_consumido_sync":
            return None
        if n == "inserir_leitura_publica_self_service_sync":
            return "leitura-token-teste-urlsafe-32charsmin__________"
        raise AssertionError(n)

    async def fake_core(*args: object, **kwargs: object) -> DiagnosticoResponse:
        return DiagnosticoResponse(
            id=UUID("11111111-1111-4111-8111-111111111111"),
            status="finalizado",
            plano="gratuito",
            empresa_razao_social="ACME Rascunho LTDA",
            score=ScoreCompletoSchema(
                score_geral=ScoreDimensaoSchema(valor=55.0, peso_total_aplicado=1.0),
                score_por_dimensao={
                    "fiscal": ScoreDimensaoSchema(valor=55.0, peso_total_aplicado=1.0),
                },
            ),
        )

    orig_core = dh._executar_criar_diagnostico_core
    dh._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/concluir",
                        json={
                            "resgate_token": "t" * 32,
                            "codigo": "123456",
                        },
                        headers={"Idempotency-Key": "c3d4e5f6-a7b8-9012-cdef-123456789012"},
                    )
    finally:
        dh._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "finalizado"
    assert body.get("leitura_token") == "leitura-token-teste-urlsafe-32charsmin__________"


@pytest.mark.asyncio
async def test_get_conclusao_visualizacao_404(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_diagnostico_conclusao_publica_sync":
            return None
        raise AssertionError(n)

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/self-service/conclusao-visualizacao",
                params={
                    "diagnostico_id": "11111111-1111-4111-8111-111111111111",
                    "leitura_token": "t" * 32,
                },
            )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_conclusao_visualizacao_200(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    drow = {
        "id": "22222222-2222-4222-8222-222222222222",
        "status": "finalizado",
        "empresa_razao_social": "ACME",
        "locale_relatorio": "pt-BR",
        "score_completo": {
            "score_geral": {
                "valor": 40.0,
                "peso_total_aplicado": 1.0,
                "perguntas_consideradas": [],
            },
            "score_por_dimensao": {
                "fiscal": {"valor": 40.0, "peso_total_aplicado": 1.0, "perguntas_consideradas": []},
            },
        },
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_diagnostico_conclusao_publica_sync":
            return drow
        raise AssertionError(n)

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/self-service/conclusao-visualizacao",
                params={
                    "diagnostico_id": "22222222-2222-4222-8222-222222222222",
                    "leitura_token": "t" * 32,
                },
            )
    assert r.status_code == 200
    j = r.json()
    assert j["empresa_razao_social"] == "ACME"
    assert j["score_geral"] == 40.0
    assert len(j["scores_por_dimensao"]) >= 1


@pytest.mark.asyncio
async def test_post_concluir_marcar_falha_503(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            return row
        if n == "marcar_rascunho_consumido_sync":
            raise psycopg2.OperationalError("simulated")
        raise AssertionError(n)

    async def fake_core(*args: object, **kwargs: object) -> DiagnosticoResponse:
        return DiagnosticoResponse(
            id=UUID("33333333-3333-4333-8333-333333333333"),
            status="finalizado",
            plano="gratuito",
            empresa_razao_social="ACME Rascunho LTDA",
            score=ScoreCompletoSchema(
                score_geral=ScoreDimensaoSchema(valor=50.0, peso_total_aplicado=1.0),
                score_por_dimensao={
                    "fiscal": ScoreDimensaoSchema(valor=50.0, peso_total_aplicado=1.0),
                },
            ),
        )

    orig_core = dh._executar_criar_diagnostico_core
    dh._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/concluir",
                        json={"resgate_token": "v" * 32, "codigo": "654321"},
                        headers={"Idempotency-Key": "e5f6a7b8-c9d0-1234-ef01-345678901234"},
                    )
    finally:
        dh._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_concluir_codigo_com_letras_400(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.post(
                "/diagnosticos/rascunho-self-service/concluir",
                json={"resgate_token": "w" * 32, "codigo": "12ab45"},
                headers={"Idempotency-Key": "f6a7b8c9-d0e1-2345-f012-456789012345"},
            )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_vincular_rascunho_conta_201(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="d4e5f6a7-b8c9-0123-def0-234567890123",
    )

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            return row
        if n == "marcar_rascunho_consumido_sync":
            return None
        raise AssertionError(n)

    async def fake_core(*args: object, **kwargs: object) -> DiagnosticoResponse:
        return DiagnosticoResponse(
            id=UUID("22222222-2222-4222-8222-222222222222"),
            status="finalizado",
            plano="gratuito",
            empresa_razao_social="ACME Rascunho LTDA",
            score=ScoreCompletoSchema(
                score_geral=ScoreDimensaoSchema(valor=60.0, peso_total_aplicado=1.0),
                score_por_dimensao={
                    "fiscal": ScoreDimensaoSchema(valor=60.0, peso_total_aplicado=1.0),
                },
            ),
        )

    em = codigo_store.normalizar_email(str(PAYLOAD_MIN["respondente"]["email"]))
    orig_core = dh._executar_criar_diagnostico_core
    dh._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(
                    dss,
                    "buscar_email_admin_por_id_e_tenant_postgres",
                    return_value=em,
                ):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/vincular-conta",
                        json={"resgate_token": "t" * 32},
                        headers=headers,
                    )
    finally:
        dh._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 201
    assert r.json()["id"] == "22222222-2222-4222-8222-222222222222"


@pytest.mark.asyncio
async def test_get_resumo_rascunho_503_sem_dsn_async(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = None

    with patch.object(dss, "get_settings", return_value=S()):
        r = await rascunho_async_client.get(
            "/diagnosticos/rascunho-self-service/resumo",
            headers={"X-Rascunho-Token": "x" * 8},
        )
    assert r.status_code == 503


def test_post_diagnostico_self_service_email_do_payload_diferente_403() -> None:
    ss_tid = get_settings().self_service_tenant_id
    oid = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    payload = dict(PAYLOAD_MIN)
    payload["respondente"] = {"email": "outro@test.io", "nome": "Respondente"}

    app.dependency_overrides[get_self_service_diagnostico_claims] = lambda: (
        oid,
        ss_tid,
        "confirmado@test.io",
    )
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: AsyncMock()
    mock_repo = AsyncMock()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo

    client = TestClient(app)
    try:
        resp = client.post(
            "/diagnosticos/self-service",
            json=payload,
            headers=cabecalho_post_diagnostico_self_service(email="confirmado@test.io"),
        )
    finally:
        app.dependency_overrides.pop(get_self_service_diagnostico_claims, None)
        app.dependency_overrides.pop(get_realizar_diagnostico_use_case, None)
        app.dependency_overrides.pop(get_diagnostico_repository, None)

    assert resp.status_code == 403


def test_post_vincular_leads_sem_dsn_503() -> None:
    class S:
        sync_database_url = None

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="a7b8c9d0-e1f2-3456-abcd-f78901234567",
    )
    mock_uc = AsyncMock()

    with patch.object(dss, "get_settings", return_value=S()):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers=headers,
            )
        finally:
            app.dependency_overrides.pop(get_vincular_diagnosticos_lead_self_service_use_case, None)

    assert r.status_code == 503


def test_post_vincular_leads_email_admin_vazio_403() -> None:
    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)

    mock_uc = AsyncMock()

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(dss, "buscar_email_admin_por_id_e_tenant_postgres", return_value=None),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={**headers, "Idempotency-Key": "b8c9d0e1-f2a3-4567-bcde-f89012345678"},
            )
        finally:
            app.dependency_overrides.pop(get_vincular_diagnosticos_lead_self_service_use_case, None)

    assert r.status_code == 403


def test_post_vincular_leads_sucesso_200() -> None:
    """Caminho feliz do router: use case devolve UUIDs e resposta materializa total + lista."""
    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)

    id1 = UUID("77777777-7777-4777-8777-777777777777")
    id2 = UUID("88888888-8888-4888-8888-888888888888")

    mock_uc = AsyncMock()
    mock_uc.execute.return_value = [id1, id2]

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(
            dss,
            "buscar_email_admin_por_id_e_tenant_postgres",
            return_value="admin@ok.br",
        ),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={
                    **headers,
                    "Idempotency-Key": "f0e1d2c3-b4a5-6789-affe-0fedcba98765",
                },
            )
        finally:
            app.dependency_overrides.pop(
                get_vincular_diagnosticos_lead_self_service_use_case,
                None,
            )

    assert r.status_code == 200
    body = r.json()
    assert body["total_vinculados"] == 2
    assert set(body["diagnostico_ids"]) == {
        str(id1),
        str(id2),
    }
    mock_uc.execute.assert_called_once()


def test_post_vincular_leads_value_error_do_use_case_400() -> None:
    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)

    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("tenant inválido")

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(
            dss,
            "buscar_email_admin_por_id_e_tenant_postgres",
            return_value="admin@empresa.br",
        ),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={**headers, "Idempotency-Key": "c9d0e1f2-a3b4-5678-cdef-901234567890"},
            )
        finally:
            app.dependency_overrides.pop(get_vincular_diagnosticos_lead_self_service_use_case, None)

    assert r.status_code == 400


def test_post_vincular_leads_psycopg2_no_execute_503() -> None:
    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)

    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = psycopg2.IntegrityError("simulated")

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(
            dss,
            "buscar_email_admin_por_id_e_tenant_postgres",
            return_value="lead@tst.io",
        ),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={**headers, "Idempotency-Key": "d0e1f2a3-b4c5-6789-def0-a12345678901"},
            )
        finally:
            app.dependency_overrides.pop(get_vincular_diagnosticos_lead_self_service_use_case, None)

    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_concluir_sem_dsn_503_async(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = None
        self_service_tenant_id = uuid4()

    with patch.object(dss, "get_settings", return_value=S()):
        r = await rascunho_async_client.post(
            "/diagnosticos/rascunho-self-service/concluir",
            json={"resgate_token": "t" * 32, "codigo": "123456"},
            headers={"Idempotency-Key": "f3a4b5c6-d7e8-9012-bcde-f456789abcde"},
        )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_get_conclusao_visualizacao_sem_dsn_503(rascunho_async_client: AsyncClient) -> None:
    class S:
        sync_database_url = None
        self_service_tenant_id = uuid4()

    with patch.object(dss, "get_settings", return_value=S()):
        r = await rascunho_async_client.get(
            "/diagnosticos/self-service/conclusao-visualizacao",
            params={
                "diagnostico_id": "11111111-1111-4111-8111-111111111111",
                "leitura_token": "t" * 32,
            },
        )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_get_resumo_payload_invalido_500_via_helper(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return {"payload_json": 12345, "email_norm": "x@y.com", "expira_em": datetime.now(UTC)}
        raise AssertionError(getattr(fn, "__name__", fn))

    orig_fn = dh._payload_json_como_dict

    def _ret_none(_blob: object) -> None:
        return None

    try:
        dh._payload_json_como_dict = _ret_none
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                r = await rascunho_async_client.get(
                    "/diagnosticos/rascunho-self-service/resumo",
                    headers={"X-Rascunho-Token": "z" * 24},
                )
    finally:
        dh._payload_json_como_dict = orig_fn

    assert r.status_code == 500


def test_post_vincular_conta_sem_dsn_503() -> None:
    """Materializar no tenant JWT exige Postgres para ler rascunho."""

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="a1b2c3d5-e6f7-8901-bcde-fabcdef01234",
    )

    class S:
        sync_database_url = None

    app.dependency_overrides[get_diagnostico_repository] = lambda: AsyncMock()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: AsyncMock()
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            r = TestClient(app).post(
                "/diagnosticos/rascunho-self-service/vincular-conta",
                json={"resgate_token": "r" * 32},
                headers=headers,
            )
    finally:
        app.dependency_overrides.pop(get_diagnostico_repository, None)
        app.dependency_overrides.pop(get_realizar_diagnostico_use_case, None)

    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_rascunho_insert_psycopg2_503(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()
        app_env = "test"

    async def fake_to_thread_raise_fn(_fn: object, /, *_a: object, **_k: object) -> None:
        raise psycopg2.InterfaceError("falha de insert")

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread_raise_fn):
            r = await rascunho_async_client.post(
                "/diagnosticos/rascunho-self-service",
                json=PAYLOAD_MIN,
                headers={"Idempotency-Key": "g4h5i6j7-k8l9-0123-mnop-q12345678901"},
            )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_get_resumo_expira_em_naive_timezone_utc(
    rascunho_async_client: AsyncClient,
) -> None:
    """Datas sem tzinfo devem ganhar UTC (alinha cliente iOS/pg)."""

    class S:
        sync_database_url = "postgresql://x"

    exp_naive = datetime.now(UTC).replace(tzinfo=None)

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return {
                "payload_json": {"empresa": {"razao_social": "Tz SA"}},
                "email_norm": "tz@corp.io",
                "expira_em": exp_naive,
            }
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "naive" + "x" * 20},
            )
    assert r.status_code == 200
    assert r.json().get("respondente_email") == "tz@corp.io"


@pytest.mark.asyncio
async def test_post_concluir_otp_invalido_400_sem_core(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    row_ok = {
        "id": str(uuid4()),
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row_ok
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss.codigo_store, "validar_e_consumir", return_value=False):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/concluir",
                    json={
                        "resgate_token": "q" * 32,
                        "codigo": "999999",
                    },
                    headers={"Idempotency-Key": "h5i6j7k8-l9m0-1234-nopq-r23456789012"},
                )
    assert r.status_code == 400


def test_post_vincular_leads_buscar_email_psycopg2_503() -> None:
    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)
    mock_uc = AsyncMock()

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(
            dss,
            "buscar_email_admin_por_id_e_tenant_postgres",
            side_effect=psycopg2.InterfaceError("read only"),
        ),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={**headers, "Idempotency-Key": "e1f2a3b4-c5d6-7890-ef01-b23456789012"},
            )
        finally:
            app.dependency_overrides.pop(get_vincular_diagnosticos_lead_self_service_use_case, None)

    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_concluir_primeira_busca_sem_rascunho_400(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> None:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return None
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.post(
                "/diagnosticos/rascunho-self-service/concluir",
                json={"resgate_token": "n" * 32, "codigo": "123456"},
                headers={"Idempotency-Key": "i7j8k9l0-m1n2-3456-opqr-s34567890123"},
            )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_concluir_segunda_busca_sem_rascunho_apos_otp_400(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row_ok = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    chamadas = {"n": 0}

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            chamadas["n"] += 1
            return row_ok if chamadas["n"] == 1 else None
        raise AssertionError(n)

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/concluir",
                    json={"resgate_token": "o" * 32, "codigo": "111111"},
                    headers={"Idempotency-Key": "j8k9l0m1-n2o3-4567-pqrs-t45678901234"},
                )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_concluir_payload_json_inconsistente_500(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": 999,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/concluir",
                    json={"resgate_token": "p" * 32, "codigo": "222222"},
                    headers={"Idempotency-Key": "k9l0m1n2-o3p4-5678-qrst-u56789012345"},
                )
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_post_concluir_email_respondente_diferente_rascunho_403(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    email_rasc = codigo_store.normalizar_email("fixo@rascunho.br")
    payload_outro = dict(PAYLOAD_MIN)
    payload_outro["respondente"] = {"email": "outro@mail.br", "nome": "X"}
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": email_rasc,
        "payload_json": payload_outro,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/concluir",
                    json={"resgate_token": "q" * 32, "codigo": "333333"},
                    headers={"Idempotency-Key": "l0m1n2o3-p4q5-6789-rstu-v67890123456"},
                )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_post_concluir_inserir_leitura_publica_falha_503(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            return row
        if n == "marcar_rascunho_consumido_sync":
            return None
        if n == "inserir_leitura_publica_self_service_sync":
            raise psycopg2.ProgrammingError("sim insert leitura")
        raise AssertionError(n)

    async def fake_core(*_a: object, **_k: object) -> DiagnosticoResponse:
        return DiagnosticoResponse(
            id=UUID("44444444-4444-4444-8444-444444444444"),
            status="finalizado",
            plano="gratuito",
            empresa_razao_social="ACME",
            score=ScoreCompletoSchema(
                score_geral=ScoreDimensaoSchema(valor=50.0, peso_total_aplicado=1.0),
                score_por_dimensao={
                    "fiscal": ScoreDimensaoSchema(valor=50.0, peso_total_aplicado=1.0),
                },
            ),
        )

    orig_core = dh._executar_criar_diagnostico_core
    dh._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(dss.codigo_store, "validar_e_consumir", return_value=True):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/concluir",
                        json={"resgate_token": "r" * 32, "codigo": "444444"},
                        headers={"Idempotency-Key": "m1n2o3p4-q5r6-789a-stuv-w78901234567"},
                    )
    finally:
        dh._executar_criar_diagnostico_core = orig_core

    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_vincular_conta_sem_rascunho_400(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="n2o3p4q5-r6s7-890b-tuvw-x89012345678",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> None:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return None
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(
                dss,
                "buscar_email_admin_por_id_e_tenant_postgres",
                return_value="admin@test.io",
            ):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/vincular-conta",
                    json={"resgate_token": "s" * 32},
                    headers=headers,
                )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_vincular_conta_lookup_admin_psycopg_503(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="o3p4q5r6-s7t8-901c-vwxy-y90123456789",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(
                dss,
                "buscar_email_admin_por_id_e_tenant_postgres",
                side_effect=psycopg2.DatabaseError("lookup falhou"),
            ):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/vincular-conta",
                    json={"resgate_token": "t" * 32},
                    headers=headers,
                )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_vincular_conta_sem_email_admin_403(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="p4q5r6s7-t8u9-012d-wxyz-z0123456789a",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss, "buscar_email_admin_por_id_e_tenant_postgres", return_value=""):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/vincular-conta",
                    json={"resgate_token": "u" * 32},
                    headers=headers,
                )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_post_vincular_conta_payload_inconsistente_500(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    rid = str(uuid4())
    em = codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"])
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": em,
        "payload_json": None,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="q5r6s7t8-u9v0-123e-xyza-a1234567890b",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(dss, "buscar_email_admin_por_id_e_tenant_postgres", return_value=em):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/vincular-conta",
                    json={"resgate_token": "v" * 32},
                    headers=headers,
                )
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_post_vincular_conta_email_admin_diferente_respondente_403(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    rid = str(uuid4())
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"]),
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="r6s7t8u9-v0w1-234f-yzab-b2345678901c",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return row
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dss, "get_settings", return_value=S()):
        with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
            with patch.object(
                dss,
                "buscar_email_admin_por_id_e_tenant_postgres",
                return_value="consultor_alien@test.io",
            ):
                r = await rascunho_async_client.post(
                    "/diagnosticos/rascunho-self-service/vincular-conta",
                    json={"resgate_token": "w" * 32},
                    headers=headers,
                )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_post_vincular_conta_marcar_consumido_falha_503(
    rascunho_async_client: AsyncClient,
) -> None:
    class S:
        sync_database_url = "postgresql://x"

    uid = uuid4()
    tid = uuid4()
    rid = str(uuid4())
    em = codigo_store.normalizar_email(PAYLOAD_MIN["respondente"]["email"])
    row = {
        "id": rid,
        "tenant_id": str(uuid4()),
        "email_norm": em,
        "payload_json": PAYLOAD_MIN,
        "expira_em": datetime.now(UTC) + timedelta(hours=1),
        "consumido_em": None,
    }
    headers = cabecalho_post_diagnostico(
        usuario_id=uid,
        tenant_id=tid,
        idempotency_key="s7t8u9v0-w1x2-345g-zabc-c3456789012d",
    )

    async def fake_to_thread(fn: object, /, *_a: object, **_k: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_rascunho_ativo_por_token_sync":
            return row
        if n == "marcar_rascunho_consumido_sync":
            raise psycopg2.OperationalError("erro ao fechar")
        raise AssertionError(n)

    async def fake_core(*_a: object, **_k: object) -> DiagnosticoResponse:
        return DiagnosticoResponse(
            id=UUID("55555555-5555-5555-8555-555555555555"),
            status="finalizado",
            plano="gratuito",
            empresa_razao_social="ACME Rascunho LTDA",
            score=ScoreCompletoSchema(
                score_geral=ScoreDimensaoSchema(valor=60.0, peso_total_aplicado=1.0),
                score_por_dimensao={
                    "fiscal": ScoreDimensaoSchema(valor=60.0, peso_total_aplicado=1.0),
                },
            ),
        )

    orig_core = dh._executar_criar_diagnostico_core
    dh._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dss, "get_settings", return_value=S()):
            with patch.object(dss.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(
                    dss,
                    "buscar_email_admin_por_id_e_tenant_postgres",
                    return_value=em,
                ):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/vincular-conta",
                        json={"resgate_token": "y" * 32},
                        headers=headers,
                    )
    finally:
        dh._executar_criar_diagnostico_core = orig_core

    assert r.status_code == 503


def test_post_vincular_leads_execucao_use_case_psycopg_503() -> None:
    """Ramo ``except psycopg2.Error`` após chamada ao use case em vincular leads."""

    class S:
        sync_database_url = "postgresql://local"
        self_service_tenant_id = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")

    uid = uuid4()
    tid = uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = psycopg2.OperationalError("update falhou")

    with (
        patch.object(dss, "get_settings", return_value=S()),
        patch.object(
            dss,
            "buscar_email_admin_por_id_e_tenant_postgres",
            return_value="ok@tst.io",
        ),
    ):
        app.dependency_overrides[get_vincular_diagnosticos_lead_self_service_use_case] = (
            lambda: mock_uc
        )
        try:
            r = TestClient(app).post(
                "/diagnosticos/vincular-leads-self-service",
                headers={**headers, "Idempotency-Key": "u9v0w1x2-y3z4-567i-bcde-e56789012345f"},
            )
        finally:
            app.dependency_overrides.pop(
                get_vincular_diagnosticos_lead_self_service_use_case,
                None,
            )

    assert r.status_code == 503
