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
    assert "pesos_macro_dimensao_score_geral" in data
    macros = data["pesos_macro_dimensao_score_geral"]
    assert macros["fiscal"] == 1.5
    assert macros["tecnologica"] == 1.3


@pytest.mark.asyncio
async def test_manifesto_pesos_publico(async_client):
    """M03 — manifesto de pesos do catálogo + macrodimensões (público)."""
    response = await async_client.get("/diagnosticos/manifesto-pesos")
    assert response.status_code == 200
    body = response.json()
    assert body["versao_catalogo"]
    assert len(body["perguntas"]) >= 1
    assert body["pesos_macro_dimensao"]["fiscal"] == 1.5
    assert body["perguntas"][0]["codigo"]
    assert "M02" in body.get("nota_calibracao_m02", "")


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
async def test_normativa_validar_ancora_positivo(async_client):
    """Protótipo Lexiq (N7): texto com LC 214/2025 é aceito."""
    response = await async_client.post(
        "/normativa/validar-ancora",
        json={"texto": "Conforme LC 214/2025 art. 5º."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is True
    assert body["motivo_rejeicao"] is None


@pytest.mark.asyncio
async def test_normativa_validar_ancora_negativo(async_client):
    response = await async_client.post(
        "/normativa/validar-ancora",
        json={"texto": "Melhore a governança tributária da empresa."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valido"] is False
    assert body["motivo_rejeicao"]


@pytest.mark.asyncio
async def test_listar_diagnosticos_sem_bearer_401(async_client):
    """GET /diagnosticos/ exige JWT (isolamento multi-tenant)."""
    response = await async_client.get("/diagnosticos/")
    assert response.status_code == 401


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
