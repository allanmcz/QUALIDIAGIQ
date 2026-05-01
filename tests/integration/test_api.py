import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer


# Utiliza o cliente de testes assíncrono do httpx
@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_health_check(async_client):
    """Testa se a API está online."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "qualidiagiq"}


@pytest.mark.asyncio
async def test_metodologia_endpoint(async_client):
    """Testa o endpoint público de metodologia."""
    response = await async_client.get("/diagnosticos/metodologia")
    assert response.status_code == 200
    data = response.json()
    assert "pesos_por_dimensao" in data
    assert "fiscal" in data["pesos_por_dimensao"]


@pytest.mark.asyncio
async def test_get_questionario_adaptativo(async_client):
    """GET filtrado por perfil + JWT (catálogo JSON)."""
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    headers = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)
    url = (
        "/diagnosticos/questionario"
        "?cnpj=12345678000195&razao_social=Empresa+Integracao"
        "&porte=micro&regime=simples_nacional&cnae_principal=1234567&uf=SP&setor_macro=comercio"
    )
    response = await async_client.get(url, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["versao_catalogo"] == "v1-doc-05-full-37"
    assert data["total"] == len(data["perguntas"])
    assert data["total"] >= 1
    assert data["perguntas"][0]["codigo"] == "Q-EST-001"


@pytest.mark.asyncio
async def test_get_questionario_publico_sem_jwt_200(async_client):
    """GET é público (catálogo filtrado — sem dados de tenant)."""
    url = (
        "/diagnosticos/questionario"
        "?cnpj=12345678000195&razao_social=X"
        "&porte=micro&regime=simples_nacional&cnae_principal=1234567&uf=SP&setor_macro=comercio"
    )
    response = await async_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert "perguntas" in data and data["total"] >= 1


@pytest.mark.asyncio
async def test_criar_diagnostico_sem_tenant(async_client):
    """Barra requisições sem Bearer JWT (Idempotency-Key exigido antes da auth)."""
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Empresa Teste",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
    }
    headers = {"Idempotency-Key": str(uuid.uuid4())}
    response = await async_client.post("/diagnosticos/", json=payload, headers=headers)
    assert response.status_code == 401
    assert "Bearer" in response.json()["detail"] or "Token" in response.json()["detail"]
