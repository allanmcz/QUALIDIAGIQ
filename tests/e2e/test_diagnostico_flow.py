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


class MockPdfGenerator:
    async def gerar_pdf_diagnostico(
        self, diagnostico, score_completo, recomendacao_ia: str | None
    ) -> bytes:
        return b"%PDF-1.4\nmock"


class MockStorageService:
    async def upload_pdf(
        self, tenant_id: uuid.UUID, diagnostico_id: uuid.UUID, file_bytes: bytes
    ) -> str:
        return f"https://mocked-storage.com/{tenant_id}/{diagnostico_id}.pdf"


class MockEmailService:
    def __init__(self):
        self.enviado = False

    async def enviar_email_com_relatorio(
        self, destinatario_email: str, destinatario_nome: str, pdf_url: str
    ) -> bool:
        self.enviado = True
        return True


class MockRepository:
    def __init__(self):
        self.db = {}

    async def salvar(self, diagnostico):
        self.db[diagnostico.id] = diagnostico

    async def buscar_por_id(self, diagnostico_id: uuid.UUID, tenant_id: uuid.UUID):
        return self.db.get(diagnostico_id)


@pytest.fixture
def mock_dependencies():
    """Sobrescreve dependências externas para evitar IO real de storage e email nos testes E2E."""
    mock_email = MockEmailService()
    mock_repo = MockRepository()

    app.dependency_overrides[get_storage_service] = lambda: MockStorageService()
    app.dependency_overrides[get_email_service] = lambda: mock_email
    app.dependency_overrides[get_pdf_generator] = lambda: MockPdfGenerator()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo

    yield mock_email

    app.dependency_overrides = {}


@pytest.fixture
async def e2e_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_fluxo_completo_diagnostico(e2e_client, mock_dependencies):
    """
    Simula um fluxo E2E:
    1. Cria o diagnóstico passando um Tenant ID válido.
    2. Valida se a resposta tem a URL do PDF (provida pelo storage mockado).
    3. Valida se o email foi enviado.
    4. Consulta o diagnóstico criado.
    """
    tenant_uuid = uuid.uuid4()
    headers = cabecalho_post_diagnostico(tenant_id=tenant_uuid)

    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Empresa E2E SA",
            "porte": "medio",
            "regime": "lucro_real",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "industria",
        },
        "respondente": {"email": "lead@empresa.com", "nome": "João Diretor"},
        "respostas": [
            {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4},
            {"pergunta_id": "5bd89013-2b3f-5c73-8a73-9351e114f14c", "valor": 3},
        ],
    }

    # 1. Criação do Diagnóstico
    response = await e2e_client.post("/diagnosticos/", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["status"] == "finalizado"
    assert data["empresa_razao_social"] == "Empresa E2E SA"
    assert data.get("hash_evidencia") is not None
    assert len(data["hash_evidencia"]) == 64
    assert data.get("versao_otimista") == 1

    # 2. Valida URL do PDF (resultado do MockStorageService)
    assert data["relatorio_pdf_url"] is not None
    assert "mocked-storage.com" in data["relatorio_pdf_url"]

    diagnostico_id = data["id"]

    # 3. Valida envio do E-mail
    assert mock_dependencies.enviado is True

    # 4. Consulta Diagnóstico
    get_headers = {k: v for k, v in headers.items() if k == "Authorization"}
    get_response = await e2e_client.get(f"/diagnosticos/{diagnostico_id}", headers=get_headers)
    assert get_response.status_code == 200

    get_data = get_response.json()
    assert get_data["id"] == diagnostico_id
    assert get_data["empresa_razao_social"] == "Empresa E2E SA"
    assert get_data.get("hash_evidencia") == data["hash_evidencia"]
    assert get_data.get("versao_otimista") == 1
