import pytest
from httpx import AsyncClient, ASGITransport

from src.presentation.api.main import app

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
async def test_criar_diagnostico_sem_tenant(async_client):
    """Testa se a criação de diagnóstico barra requisições sem tenant id."""
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Empresa Teste",
            "porte": "EPP",
            "regime": "SIMPLES_NACIONAL",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "COMERCIO"
        },
        "respondente": {
            "email": "teste@teste.com"
        },
        "respostas": []
    }
    response = await async_client.post("/diagnosticos/", json=payload)
    assert response.status_code == 401
    assert "X-Tenant-ID ausente" in response.json()["detail"]
