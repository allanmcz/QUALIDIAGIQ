"""Testes HTTP dos endpoints de rascunho self-service (mocks de Postgres via asyncio.to_thread)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import psycopg2
import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.email_verificacao import codigo_store
from src.presentation.api.dependencies import get_email_service, get_realizar_diagnostico_use_case
from src.presentation.api.main import app
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
)
from tests.conftest import cabecalho_post_diagnostico

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
    from src.presentation.api.routers import diagnostico_router as dr

    class S:
        sync_database_url = None
        self_service_tenant_id = uuid4()

    with patch.object(dr, "get_settings", return_value=S()):
        r = await rascunho_async_client.post(
            "/diagnosticos/rascunho-self-service",
            json=PAYLOAD_MIN,
            headers={"Idempotency-Key": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
        )
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_rascunho_201(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()
        app_env = "test"

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "inserir_rascunho_sync":
            return ("resgate-token-fixo", datetime.now(UTC))
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
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
    from src.presentation.api.routers import diagnostico_router as dr

    class S:
        sync_database_url = "postgresql://x"

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        if getattr(fn, "__name__", "") == "buscar_rascunho_ativo_por_token_sync":
            return None
        raise AssertionError(getattr(fn, "__name__", fn))

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "invalido"},
            )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_resumo_200(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

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

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
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
    from src.presentation.api.routers import diagnostico_router as dr

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

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "t" * 24},
            )
    assert r.status_code == 200
    assert r.json()["empresa_razao_social"] == "(sem razão social)"


@pytest.mark.asyncio
async def test_get_resumo_sem_expira_em_500(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

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

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.get(
                "/diagnosticos/rascunho-self-service/resumo",
                headers={"X-Rascunho-Token": "u" * 24},
            )
    assert r.status_code == 500


@pytest.mark.asyncio
async def test_post_concluir_rascunho_201(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

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

    orig_core = dr._executar_criar_diagnostico_core
    dr._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dr, "get_settings", return_value=S()):
            with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(dr.codigo_store, "validar_e_consumir", return_value=True):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/concluir",
                        json={
                            "resgate_token": "t" * 32,
                            "codigo": "123456",
                        },
                        headers={"Idempotency-Key": "c3d4e5f6-a7b8-9012-cdef-123456789012"},
                    )
    finally:
        dr._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "finalizado"
    assert body.get("leitura_token") == "leitura-token-teste-urlsafe-32charsmin__________"


@pytest.mark.asyncio
async def test_get_conclusao_visualizacao_404(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

    class S:
        sync_database_url = "postgresql://x"
        self_service_tenant_id = uuid4()

    async def fake_to_thread(fn: object, /, *args: object, **kwargs: object) -> object:
        n = getattr(fn, "__name__", "")
        if n == "buscar_diagnostico_conclusao_publica_sync":
            return None
        raise AssertionError(n)

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
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
    from src.presentation.api.routers import diagnostico_router as dr

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

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
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
    from src.presentation.api.routers import diagnostico_router as dr

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

    orig_core = dr._executar_criar_diagnostico_core
    dr._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dr, "get_settings", return_value=S()):
            with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(dr.codigo_store, "validar_e_consumir", return_value=True):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/concluir",
                        json={"resgate_token": "v" * 32, "codigo": "654321"},
                        headers={"Idempotency-Key": "e5f6a7b8-c9d0-1234-ef01-345678901234"},
                    )
    finally:
        dr._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_post_concluir_codigo_com_letras_400(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

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

    with patch.object(dr, "get_settings", return_value=S()):
        with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
            r = await rascunho_async_client.post(
                "/diagnosticos/rascunho-self-service/concluir",
                json={"resgate_token": "w" * 32, "codigo": "12ab45"},
                headers={"Idempotency-Key": "f6a7b8c9-d0e1-2345-f012-456789012345"},
            )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_post_vincular_rascunho_conta_201(rascunho_async_client: AsyncClient) -> None:
    from src.presentation.api.routers import diagnostico_router as dr

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
    orig_core = dr._executar_criar_diagnostico_core
    dr._executar_criar_diagnostico_core = fake_core
    try:
        with patch.object(dr, "get_settings", return_value=S()):
            with patch.object(dr.asyncio, "to_thread", side_effect=fake_to_thread):
                with patch.object(
                    dr,
                    "buscar_email_admin_por_id_e_tenant_postgres",
                    return_value=em,
                ):
                    r = await rascunho_async_client.post(
                        "/diagnosticos/rascunho-self-service/vincular-conta",
                        json={"resgate_token": "t" * 32},
                        headers=headers,
                    )
    finally:
        dr._executar_criar_diagnostico_core = orig_core
    assert r.status_code == 201
    assert r.json()["id"] == "22222222-2222-4222-8222-222222222222"
