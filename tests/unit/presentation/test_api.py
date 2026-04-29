import uuid
from unittest.mock import AsyncMock, MagicMock

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

    mock_resultado = MagicMock()
    mock_resultado.diagnostico.id = uuid.uuid4()
    mock_resultado.diagnostico.status.value = "finalizado"
    mock_resultado.diagnostico.empresa.razao_social = "Teste LTDA"
    
    mock_resultado.score.score_geral.valor = 100.0
    mock_resultado.score.score_geral.peso_total_aplicado = 1.0
    
    dimensao_mock = MagicMock()
    dimensao_mock.valor = 100.0
    dimensao_mock.peso_total_aplicado = 1.0
    dim_key = MagicMock()
    dim_key.value = "fiscal"
    mock_resultado.score.score_por_dimensao = {dim_key: dimensao_mock}
    
    mock_resultado.relatorio_pdf_url = None

    mock_use_case.execute.return_value = mock_resultado

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


def test_criar_diagnostico_com_header_invalido():
    payload = {"empresa": {}, "respondente": {}, "respostas": []} # Payload não importa pois falha no header
    headers = {"X-Tenant-ID": "invalid-uuid"}
    response = client.post("/diagnosticos/", json=payload, headers=headers)
    assert response.status_code == 401
    assert "Header X-Tenant-ID inválido" in response.json()["detail"]


def test_obter_diagnostico_com_sucesso():
    from src.presentation.api.dependencies import get_diagnostico_repository
    
    mock_repo = AsyncMock()
    mock_diagnostico = MagicMock()
    diagnostico_id = uuid.uuid4()
    mock_diagnostico.id = diagnostico_id
    mock_diagnostico.status.value = "finalizado"
    mock_diagnostico.empresa.razao_social = "Empresa GET LTDA"
    mock_diagnostico.relatorio_pdf_url = "http://pdf.url"
    
    mock_repo.buscar_por_id.return_value = mock_diagnostico
    
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    
    headers = {"X-Tenant-ID": str(uuid.uuid4())}
    response = client.get(f"/diagnosticos/{diagnostico_id}", headers=headers)
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(diagnostico_id)
    assert data["empresa_razao_social"] == "Empresa GET LTDA"


def test_obter_diagnostico_nao_encontrado():
    from src.presentation.api.dependencies import get_diagnostico_repository
    
    mock_repo = AsyncMock()
    mock_repo.buscar_por_id.return_value = None
    
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    
    headers = {"X-Tenant-ID": str(uuid.uuid4())}
    response = client.get(f"/diagnosticos/{uuid.uuid4()}", headers=headers)
    
    app.dependency_overrides.clear()
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Diagnóstico não encontrado"

