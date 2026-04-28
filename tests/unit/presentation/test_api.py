import uuid
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.presentation.api.dependencies import (
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.main import app

client = TestClient(app)


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "qualidiagiq"}


def test_criar_diagnostico_sem_header_falha():
    payload = {
        "empresa": {
            "cnpj": "12345678000199",
            "razao_social": "Teste",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com"},
        "respostas": [{"pergunta_id": "00000000-0000-0000-0000-000000000001", "valor": "sim"}],
    }

    response = client.post("/diagnosticos/", json=payload)
    assert response.status_code == 401
    assert "Header X-Tenant-ID ausente" in response.json()["detail"]


def test_criar_diagnostico_com_sucesso():
    # Mock do UseCase
    mock_use_case = AsyncMock()

    # Simula a estrutura do resultado
    class MockScoreDimensao:
        valor = 100.0
        peso_total_aplicado = 1.0

    class MockScore:
        score_geral = MockScoreDimensao()
        score_por_dimensao = {"fiscal": MockScoreDimensao()}

    class MockDiagnostico:
        id = uuid.uuid4()
        status = type("Status", (), {"value": "finalizado"})
        empresa = type("Empresa", (), {"razao_social": "Teste LTDA"})

    class MockResultado:
        diagnostico = MockDiagnostico()
        score = MockScore()
        relatorio_pdf_url = None

    mock_use_case.execute.return_value = MockResultado()

    # Sobrescreve a injeção de dependência na API
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_use_case

    payload = {
        "empresa": {
            "cnpj": "12345678000199",
            "razao_social": "Teste LTDA",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com"},
        "respostas": [{"pergunta_id": "00000000-0000-0000-0000-000000000001", "valor": "sim"}],
    }

    headers = {"X-Tenant-ID": str(uuid.uuid4())}
    response = client.post("/diagnosticos/", json=payload, headers=headers)

    # Restaura DI
    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "finalizado"
    assert data["score"]["score_geral"]["valor"] == 100.0
