import copy
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.application.errors import ConflitoVersaoOtimistaError
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_atualizar_checklist_m12_autoconf_use_case,
    get_current_user_tenant,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.main import app
from src.presentation.api.routers.diagnostico_router import _parse_if_match_versao
from tests.conftest import cabecalho_auth_bearer, cabecalho_post_diagnostico

client = TestClient(app)


def _diag_finalizado_micro() -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000199",
        razao_social="API PATCH LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=uuid.uuid4(),
        empresa=empresa,
        respondente=Respondente(email="patch@teste.com"),
    )
    d.finalizar(62.0)
    return d


def test_parse_if_match_versao_variants():
    assert _parse_if_match_versao("1") == 1
    assert _parse_if_match_versao('"4"') == 4
    assert _parse_if_match_versao('W/"2"') == 2


def test_parse_if_match_versao_erro():
    with pytest.raises(ValueError):
        _parse_if_match_versao(None)


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "qualidiagiq"}


def test_criar_diagnostico_sem_token_falha():
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
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
    }

    response = client.post(
        "/diagnosticos/",
        json=payload,
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 401
    detail = response.json()["detail"]
    assert "Bearer" in detail or "Token" in detail


def test_criar_diagnostico_com_sucesso():
    # Mock do UseCase
    mock_use_case = AsyncMock()

    mock_resultado = MagicMock()
    mock_resultado.diagnostico.id = uuid.uuid4()
    mock_resultado.diagnostico.status.value = "finalizado"
    mock_resultado.diagnostico.plano.value = "gratuito"
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
    mock_resultado.recomendacao_ia = None
    mock_resultado.checklist = None
    mock_resultado.matriz_impacto = None
    mock_resultado.cronograma = None
    mock_resultado.diagnostico.hash_evidencia = "a" * 64
    mock_resultado.diagnostico.versao_otimista = 1

    mock_use_case.execute.return_value = mock_resultado

    # Sobrescreve a injeção de dependência na API
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_use_case
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

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
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
    }

    response = client.post("/diagnosticos/", json=payload, headers=cabecalho_post_diagnostico())

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "finalizado"
    assert data["score"]["score_geral"]["valor"] == 100.0
    assert data["hash_evidencia"] == "a" * 64
    assert data["versao_otimista"] == 1


def test_criar_diagnostico_com_token_invalido():
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
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
    }
    headers = {
        "Authorization": "Bearer token-invalido",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    response = client.post("/diagnosticos/", json=payload, headers=headers)
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"] or "expirado" in response.json()["detail"]


def test_obter_diagnostico_com_sucesso():
    from src.presentation.api.dependencies import get_diagnostico_repository

    mock_repo = AsyncMock()
    mock_diagnostico = MagicMock()
    diagnostico_id = uuid.uuid4()
    mock_diagnostico.id = diagnostico_id
    mock_diagnostico.status.value = "finalizado"
    mock_diagnostico.plano.value = "gratuito"
    mock_diagnostico.empresa.razao_social = "Empresa GET LTDA"
    mock_diagnostico.relatorio_pdf_url = "http://pdf.url"

    mock_repo.buscar_por_id.return_value = mock_diagnostico

    uid = uuid.uuid4()
    tid = uuid.uuid4()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.get(
        f"/diagnosticos/{diagnostico_id}",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(diagnostico_id)
    assert data["empresa_razao_social"] == "Empresa GET LTDA"


def test_patch_relatorio_sem_if_match_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}",
        json={"relatorio_pdf_url": "https://x/p.pdf"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "If-Match" in response.json()["detail"]
    mock_uc.execute.assert_not_called()


def test_patch_relatorio_conflito_412():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ConflitoVersaoOtimistaError("versão 1 obsoleta")
    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}",
        json={"relatorio_pdf_url": "https://x/p.pdf"},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": "1",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 412


def test_patch_relatorio_sucesso():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_in = _diag_finalizado_micro()
    d_in.tenant_id = tid
    d_out = copy.deepcopy(d_in)
    d_out.anexar_relatorio("https://storage/rel.pdf")
    d_out.versao_otimista = 2

    mock_uc = AsyncMock()
    mock_uc.execute.return_value = d_out

    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.patch(
        f"/diagnosticos/{d_in.id}",
        json={"relatorio_pdf_url": "https://storage/rel.pdf"},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["relatorio_pdf_url"] == "https://storage/rel.pdf"
    assert body["versao_otimista"] == 2


def test_patch_checklist_m12_sem_if_match_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [False] * 10},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "If-Match" in response.json()["detail"]
    mock_uc.execute.assert_not_called()


def test_patch_checklist_m12_conflito_412():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ConflitoVersaoOtimistaError("versão obsoleta")
    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [True] * 10},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": "1",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 412


def test_patch_checklist_m12_sucesso():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_in = _diag_finalizado_micro()
    d_in.tenant_id = tid
    d_out = copy.deepcopy(d_in)
    d_out.definir_checklist_m12_autoconf([True] + [False] * 9)
    d_out.versao_otimista = 2

    mock_uc = AsyncMock()
    mock_uc.execute.return_value = d_out

    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    payload = {"checklist_m12_autoconf": [True] + [False] * 9}
    response = client.patch(
        f"/diagnosticos/{d_in.id}/checklist-m12-autoconf",
        json=payload,
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["versao_otimista"] == 2
    assert body["checklist_m12_autoconf"] == [True] + [False] * 9


def test_listar_diagnosticos_resumo():
    from src.presentation.api.dependencies import get_diagnostico_repository

    tid = uuid.uuid4()
    uid = uuid.uuid4()
    d1 = _diag_finalizado_micro()
    d1.tenant_id = tid
    d2 = copy.deepcopy(d1)
    d2.id = uuid.uuid4()
    d2.empresa = EmpresaInfo(
        cnpj="98765432000111",
        razao_social="Outra LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )

    mock_repo = AsyncMock()
    mock_repo.listar_por_tenant.return_value = [d1, d2]

    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.get(
        "/diagnosticos/?limit=10&offset=0",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["empresa_razao_social"] == "API PATCH LTDA"
    assert body[0]["score_geral"] == 62.0
    assert body[1]["empresa_razao_social"] == "Outra LTDA"
    mock_repo.listar_por_tenant.assert_awaited_once_with(tid, limit=10, offset=0)


def test_obter_diagnostico_nao_encontrado():
    from src.presentation.api.dependencies import get_diagnostico_repository

    mock_repo = AsyncMock()
    mock_repo.buscar_por_id.return_value = None

    uid = uuid.uuid4()
    tid = uuid.uuid4()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid)

    response = client.get(
        f"/diagnosticos/{uuid.uuid4()}",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Diagnóstico não encontrado"
