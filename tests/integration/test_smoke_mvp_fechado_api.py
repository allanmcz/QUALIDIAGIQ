"""
Smoke automatizado — alinhado a ``docs/operacao/SMOKE_MVP_FECHADO.md`` (passos API em CI).

Itens não cobertos aqui: login real contra Supabase (passo 2), wizard Playwright (passo 3),
PDF WeasyPrint real (passo 8) — ver e2e Playwright e job backend com migrações.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_email_service,
    get_pdf_generator,
    get_storage_service,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_post_diagnostico
from tests.e2e.test_diagnostico_flow import (
    MockEmailService,
    MockPdfGenerator,
    MockRepository,
    MockStorageService,
)


@pytest.fixture
def smoke_overrides():
    mock_email = MockEmailService()
    mock_repo = MockRepository()

    app.dependency_overrides[get_storage_service] = lambda: MockStorageService()
    app.dependency_overrides[get_email_service] = lambda: mock_email
    app.dependency_overrides[get_pdf_generator] = lambda: MockPdfGenerator()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo

    yield mock_email

    app.dependency_overrides = {}


@pytest.fixture
async def smoke_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
@pytest.mark.mvp_gate
async def test_smoke_health_e_trace_id(smoke_client, smoke_overrides):
    del smoke_overrides
    r1 = await smoke_client.get("/health")
    assert r1.status_code == 200
    assert r1.headers.get("X-Trace-Id")

    r2 = await smoke_client.get("/health", headers={"X-Trace-Id": "smoke-mvp-automated"})
    assert r2.status_code == 200
    assert r2.headers.get("X-Trace-Id") == "smoke-mvp-automated"


@pytest.mark.asyncio
@pytest.mark.mvp_gate
async def test_smoke_post_lista_detalhe_com_aceite_lgpd(smoke_client, smoke_overrides):
    """Passos 4-6 do smoke manual (JWT sintético = equivalência ao bearer após login)."""
    tenant_uuid = uuid.uuid4()
    headers = cabecalho_post_diagnostico(tenant_id=tenant_uuid)

    # Mesmo perfil do e2e (questionário expandido + respostas mínimas válidas).
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Smoke MVP SA",
            "porte": "medio",
            "regime": "lucro_real",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "industria",
        },
        "respondente": {"email": "smoke-mvp@example.com", "nome": "Smoke Tester"},
        "respostas": [
            {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4},
            {"pergunta_id": "5bd89013-2b3f-5c73-8a73-9351e114f14c", "valor": 3},
        ],
        "aceite_termos_privacidade": True,
    }

    post_r = await smoke_client.post("/diagnosticos/", json=payload, headers=headers)
    assert post_r.status_code == 201
    body = post_r.json()
    assert body.get("aceite_termos_privacidade_em") is not None
    diag_id = body["id"]

    list_r = await smoke_client.get(
        "/diagnosticos/",
        headers={"Authorization": headers["Authorization"]},
    )
    assert list_r.status_code == 200
    lista = list_r.json()
    ids = {str(row["id"]) for row in lista}
    assert str(diag_id) in ids

    get_r = await smoke_client.get(
        f"/diagnosticos/{diag_id}",
        headers={"Authorization": headers["Authorization"]},
    )
    assert get_r.status_code == 200
    det = get_r.json()
    assert det["id"] == diag_id
    assert det.get("hash_evidencia") is not None
    assert det.get("versao_otimista") is not None

    assert smoke_overrides.enviado is True
