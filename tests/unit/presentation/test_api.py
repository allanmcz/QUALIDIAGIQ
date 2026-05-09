import copy
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_atualizar_checklist_m12_autoconf_use_case,
    get_atualizar_quadro_implantacao_use_case,
    get_atualizar_subtarefa_plano_diagnostico_use_case,
    get_criar_subtarefa_plano_diagnostico_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.main import app
from src.presentation.api.routers.diagnostico_helpers import _parse_if_match_versao
from tests.conftest import (
    cabecalho_auth_bearer,
    cabecalho_post_diagnostico,
    cabecalho_post_diagnostico_self_service,
)

client = TestClient(app)


def _score_completo_snapshot_http(score_geral: float, dim_fiscal: float) -> ScoreCompleto:
    """Snapshot mínimo para ``_montar_diagnostico_response`` (motor HTTP legado)."""
    return ScoreCompleto(
        score_geral=ScoreNumerico(valor=score_geral, peso_total_aplicado=1.0),
        score_por_dimensao={
            Dimensao.FISCAL: ScoreNumerico(valor=dim_fiscal, peso_total_aplicado=1.0),
        },
    )


def _diag_finalizado_micro() -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000195",
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
    assert response.headers.get("X-Trace-Id")


def test_mock_storage_pdf_inline():
    """GET /mock-storage devolve PDF colocado no cache (fallback Storage)."""
    import uuid

    from src.infrastructure.storage.mock_pdf_bytes_cache import registrar_pdf_mock

    tid = uuid.UUID("44444444-4444-4444-8444-444444444444")
    did = uuid.UUID("090c0f6a-7fcb-4015-bdfa-37bb9a545740")
    nome = f"{did}.pdf"
    registrar_pdf_mock(f"{tid}/{nome}", b"%PDF-1.4 smoke")
    r = client.get(f"/mock-storage/{tid}/{nome}")
    assert r.status_code == 200
    assert r.headers.get("content-type") == "application/pdf"
    assert "inline" in (r.headers.get("content-disposition") or "").lower()
    assert b"%PDF" in r.content


def test_mock_storage_rejeita_traversal():
    import uuid

    tid = uuid.UUID("44444444-4444-4444-8444-444444444444")
    r = client.get(f"/mock-storage/{tid}/..evil.pdf")
    assert r.status_code == 400


def test_healthcheck_repasse_x_trace_id():
    response = client.get("/health", headers={"X-Trace-Id": "trace-fixo-e2e"})
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id") == "trace-fixo-e2e"


def test_criar_diagnostico_sem_token_falha():
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Teste",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com", "nome": "Respondente QA"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
        "aceite_termos_privacidade": True,
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
    mock_resultado.diagnostico.empresa.faixa_faturamento = None

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
    mock_resultado.diagnostico.aceite_termos_privacidade_em = datetime.now(UTC)
    mock_resultado.diagnostico.locale_relatorio = "pt-BR"
    mock_resultado.diagnostico.relatorio_pdf_url = None
    mock_resultado.diagnostico.score_completo_snapshot = _score_completo_snapshot_http(100.0, 100.0)

    mock_use_case.execute.return_value = mock_resultado

    # Sobrescreve a injeção de dependência na API
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_use_case
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Teste LTDA",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com", "nome": "Respondente QA"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
        "aceite_termos_privacidade": True,
    }

    response = client.post("/diagnosticos/", json=payload, headers=cabecalho_post_diagnostico())

    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "finalizado"
    assert data["score"]["score_geral"]["valor"] == 100.0
    assert data["hash_evidencia"] == "a" * 64
    assert data["versao_otimista"] == 1
    assert data.get("aceite_termos_privacidade_em") is not None
    assert data.get("locale_relatorio") == "pt-BR"


def test_criar_diagnostico_sem_aceite_lgpd_422():
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Teste",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com", "nome": "Respondente QA"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
        "aceite_termos_privacidade": False,
    }
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    response = client.post("/diagnosticos/", json=payload, headers=cabecalho_post_diagnostico())
    app.dependency_overrides.clear()
    assert response.status_code == 422
    mock_uc.execute.assert_not_called()


def test_criar_diagnostico_com_token_invalido():
    mock_uc = AsyncMock()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    payload = {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Teste",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": "teste@teste.com", "nome": "Respondente QA"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
        "aceite_termos_privacidade": True,
    }
    headers = {
        "Authorization": "Bearer token-invalido",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    response = client.post("/diagnosticos/", json=payload, headers=headers)
    app.dependency_overrides.clear()
    assert response.status_code == 401
    assert "inválido" in response.json()["detail"] or "expirado" in response.json()["detail"]


def _payload_diagnostico_minimo_api(*, email: str = "teste@teste.com") -> dict:
    return {
        "empresa": {
            "cnpj": "12345678000195",
            "razao_social": "Teste LTDA",
            "porte": "micro",
            "regime": "simples_nacional",
            "cnae_principal": "1234567",
            "uf": "SP",
            "setor_macro": "comercio",
        },
        "respondente": {"email": email, "nome": "Respondente QA"},
        "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
        "aceite_termos_privacidade": True,
    }


def test_criar_diagnostico_self_service_sem_token_falha():
    response = client.post(
        "/diagnosticos/self-service",
        json=_payload_diagnostico_minimo_api(),
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 401


def test_criar_diagnostico_self_service_email_diferente_403():
    from src.infrastructure.config.settings import get_settings
    from src.presentation.api.dependencies import (
        get_realizar_diagnostico_use_case,
        get_self_service_diagnostico_claims,
    )

    mock_uc = AsyncMock()
    settings = get_settings()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_self_service_diagnostico_claims] = lambda: (
        uuid.uuid4(),
        settings.self_service_tenant_id,
        "um@teste.com",
    )
    response = client.post(
        "/diagnosticos/self-service",
        json=_payload_diagnostico_minimo_api(email="dois@teste.com"),
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    app.dependency_overrides.clear()
    assert response.status_code == 403
    assert "OTP" in response.json()["detail"] or "e-mail" in response.json()["detail"].lower()
    mock_uc.execute.assert_not_called()


def test_criar_diagnostico_self_service_jwt_valido_sucesso():
    from src.presentation.api.dependencies import get_realizar_diagnostico_use_case

    mock_use_case = AsyncMock()
    mock_resultado = MagicMock()
    mock_resultado.diagnostico.id = uuid.uuid4()
    mock_resultado.diagnostico.status.value = "finalizado"
    mock_resultado.diagnostico.plano.value = "gratuito"
    mock_resultado.diagnostico.empresa.razao_social = "Teste LTDA"
    mock_resultado.diagnostico.empresa.faixa_faturamento = None
    mock_resultado.score.score_geral.valor = 88.5
    mock_resultado.score.score_geral.peso_total_aplicado = 1.0
    dimensao_mock = MagicMock()
    dimensao_mock.valor = 90.0
    dimensao_mock.peso_total_aplicado = 1.0
    dim_key = MagicMock()
    dim_key.value = "fiscal"
    mock_resultado.score.score_por_dimensao = {dim_key: dimensao_mock}
    mock_resultado.relatorio_pdf_url = None
    mock_resultado.recomendacao_ia = None
    mock_resultado.checklist = None
    mock_resultado.matriz_impacto = None
    mock_resultado.cronograma = None
    mock_resultado.diagnostico.hash_evidencia = "b" * 64
    mock_resultado.diagnostico.versao_otimista = 2
    mock_resultado.diagnostico.aceite_termos_privacidade_em = datetime.now(UTC)
    mock_resultado.diagnostico.locale_relatorio = "pt-BR"
    mock_resultado.diagnostico.relatorio_pdf_url = None
    mock_resultado.diagnostico.score_completo_snapshot = _score_completo_snapshot_http(88.5, 90.0)
    mock_use_case.execute.return_value = mock_resultado

    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_use_case

    response = client.post(
        "/diagnosticos/self-service",
        json=_payload_diagnostico_minimo_api(email="lead@self.br"),
        headers=cabecalho_post_diagnostico_self_service(email="lead@self.br"),
    )
    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "finalizado"
    assert data["score"]["score_geral"]["valor"] == 88.5


def test_obter_diagnostico_com_sucesso():
    from src.presentation.api.dependencies import get_diagnostico_repository

    mock_repo = AsyncMock()
    mock_diagnostico = MagicMock()
    diagnostico_id = uuid.uuid4()
    mock_diagnostico.id = diagnostico_id
    mock_diagnostico.status.value = "finalizado"
    mock_diagnostico.plano.value = "gratuito"
    mock_diagnostico.empresa.razao_social = "Empresa GET LTDA"
    mock_diagnostico.empresa.faixa_faturamento = None
    mock_diagnostico.relatorio_pdf_url = "http://pdf.url"
    mock_diagnostico.locale_relatorio = "pt-BR"

    mock_repo.buscar_por_id.return_value = mock_diagnostico
    mock_repo.buscar_plano_painel_serializado = AsyncMock(return_value=None)

    uid = uuid.uuid4()
    tid = uuid.uuid4()
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.get(
        f"/diagnosticos/{diagnostico_id}",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(diagnostico_id)
    assert data["empresa_razao_social"] == "Empresa GET LTDA"
    assert data["locale_relatorio"] == "pt-BR"


def test_patch_relatorio_sem_if_match_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [1] * 10},
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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [5] * 10},
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
    d_out.definir_checklist_m12_autoconf([5] + [1] * 9)
    d_out.versao_otimista = 2

    mock_uc = AsyncMock()
    mock_uc.execute.return_value = d_out

    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    payload = {"checklist_m12_autoconf": [5] + [1] * 9}
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
    assert body["checklist_m12_autoconf"] == [5] + [1] * 9


def test_listar_diagnosticos_resumo():
    from src.presentation.api.dependencies import get_diagnostico_repository

    tid = uuid.uuid4()
    uid = uuid.uuid4()
    d1 = _diag_finalizado_micro()
    d1.tenant_id = tid
    d2 = copy.deepcopy(d1)
    d2.id = uuid.uuid4()
    d2.empresa = EmpresaInfo(
        cnpj="11222333000181",
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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

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
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.get(
        f"/diagnosticos/{uuid.uuid4()}",
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Diagnóstico não encontrado"


def test_patch_relatorio_pdf_use_case_value_error_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("URL de relatório rejeitada")

    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}",
        json={"relatorio_pdf_url": "https://exemplo/arquivo.doc"},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "relatório" in response.json()["detail"]


def test_patch_relatorio_pdf_diagnostico_nao_encontrado_404():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = DiagnosticoNaoEncontradoError()

    app.dependency_overrides[get_anexar_relatorio_otimista_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}",
        json={"relatorio_pdf_url": "https://x/y.pdf"},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["detail"] == "Diagnóstico não encontrado"


def test_patch_checklist_m12_use_case_value_error_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("lista com tamanho inválido")

    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [3] * 10},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"]


def test_patch_checklist_m12_diagnostico_nao_encontrado_404():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = DiagnosticoNaoEncontradoError()

    app.dependency_overrides[get_atualizar_checklist_m12_autoconf_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/checklist-m12-autoconf",
        json={"checklist_m12_autoconf": [3] * 10},
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_patch_quadro_implantacao_conflito_412():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ConflitoVersaoOtimistaError("versão esperada diferente")

    app.dependency_overrides[get_atualizar_quadro_implantacao_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/quadro-implantacao-anotacoes",
        json={
            "quadro_implantacao_anotacoes": {
                "f0_a0": {
                    "comentario": "",
                    "comentarios": [],
                    "prazo_meta": "",
                    "descricao_personalizada": "",
                },
            },
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": "1",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 412


def test_patch_quadro_implantacao_diagnostico_nao_encontrado_404_quadro():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = DiagnosticoNaoEncontradoError()

    app.dependency_overrides[get_atualizar_quadro_implantacao_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/quadro-implantacao-anotacoes",
        json={
            "quadro_implantacao_anotacoes": {
                "f0_a0": {
                    "comentario": "",
                    "comentarios": [],
                    "prazo_meta": "",
                    "descricao_personalizada": "",
                },
            },
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": "1",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_patch_quadro_implantacao_use_case_value_error_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("quadro inválido")

    app.dependency_overrides[get_atualizar_quadro_implantacao_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/quadro-implantacao-anotacoes",
        json={
            "quadro_implantacao_anotacoes": {
                "f0_a0": {
                    "comentario": "",
                    "comentarios": [],
                    "prazo_meta": "",
                    "descricao_personalizada": "",
                },
            },
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": "1",
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_patch_quadro_implantacao_sem_if_match_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()

    app.dependency_overrides[get_atualizar_quadro_implantacao_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{uuid.uuid4()}/quadro-implantacao-anotacoes",
        json={
            "quadro_implantacao_anotacoes": {
                "f2_a3": {
                    "comentario": "",
                    "comentarios": [],
                    "prazo_meta": "",
                    "descricao_personalizada": "",
                },
            },
        },
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "If-Match" in response.json()["detail"]
    mock_uc.execute.assert_not_called()


def test_patch_quadro_implantacao_comentario_unico_para_lista():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_out = copy.deepcopy(_diag_finalizado_micro())
    d_out.tenant_id = tid
    d_out.versao_otimista = 2

    mock_uc = AsyncMock()
    mock_uc.execute.return_value = d_out
    mock_repo = AsyncMock()
    mock_repo.buscar_plano_painel_serializado = AsyncMock(return_value=None)

    app.dependency_overrides[get_atualizar_quadro_implantacao_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    response = client.patch(
        f"/diagnosticos/{d_out.id}/quadro-implantacao-anotacoes",
        json={
            "quadro_implantacao_anotacoes": {
                "f1_a0": {
                    "comentario": "  nota única  ",
                    "comentarios": [],
                    "prazo_meta": "",
                    "descricao_personalizada": "  ",
                },
            },
        },
        headers={
            **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
            "If-Match": '"1"',
        },
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    cmd = mock_uc.execute.await_args.args[0]
    assert cmd.quadro_implantacao_anotacoes["f1_a0"]["comentarios"] == ["nota única"]


def test_post_subtarefa_plano_use_case_value_error_400():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("ação inexistente")

    app.dependency_overrides[get_criar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    plano_acao = uuid.uuid4()
    response = client.post(
        f"/diagnosticos/{did}/plano-acoes/{plano_acao}/subtarefas",
        json={"titulo": "Sub A", "ordem": 0},
        headers=cabecalho_post_diagnostico(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "inexistente" in response.json()["detail"]


def test_post_subtarefa_repo_nao_encontra_diagnostico_404():
    uid = uuid.uuid4()
    tid = uuid.uuid4()

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=None)

    mock_repo = AsyncMock()
    mock_repo.buscar_por_id = AsyncMock(return_value=None)

    app.dependency_overrides[get_criar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    plano_acao = uuid.uuid4()
    response = client.post(
        f"/diagnosticos/{did}/plano-acoes/{plano_acao}/subtarefas",
        json={"titulo": "Sub B", "ordem": 1},
        headers=cabecalho_post_diagnostico(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_patch_subtarefa_plano_diag_inexistente_404():
    uid = uuid.uuid4()
    tid = uuid.uuid4()

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=None)

    mock_repo = AsyncMock()
    mock_repo.buscar_por_id = AsyncMock(return_value=None)

    app.dependency_overrides[get_atualizar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    subtarefa = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/plano-subtarefas/{subtarefa}",
        json={"titulo": "Nova"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 404


def test_patch_subtarefa_plano_bad_request_via_use_case():
    uid = uuid.uuid4()
    tid = uuid.uuid4()

    mock_uc = AsyncMock()
    mock_uc.execute.side_effect = ValueError("transição ilegal")

    app.dependency_overrides[get_atualizar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    did = uuid.uuid4()
    subtarefa = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{did}/plano-subtarefas/{subtarefa}",
        json={"titulo": "X"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 400


def test_post_subtarefa_plano_sucesso_201():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_snap = copy.deepcopy(_diag_finalizado_micro())
    d_snap.tenant_id = tid

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=None)

    mock_repo = AsyncMock()
    mock_repo.buscar_por_id = AsyncMock(return_value=d_snap)
    mock_repo.buscar_plano_painel_serializado = AsyncMock(return_value=None)

    app.dependency_overrides[get_criar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    plano_acao = uuid.uuid4()
    response = client.post(
        f"/diagnosticos/{d_snap.id}/plano-acoes/{plano_acao}/subtarefas",
        json={"titulo": "Subtarefa criada", "ordem": 2},
        headers=cabecalho_post_diagnostico(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(d_snap.id)
    mock_uc.execute.assert_awaited_once()


def test_patch_subtarefa_plano_sucesso_200():
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_snap = copy.deepcopy(_diag_finalizado_micro())
    d_snap.tenant_id = tid

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(return_value=None)

    mock_repo = AsyncMock()
    mock_repo.buscar_por_id = AsyncMock(return_value=d_snap)
    mock_repo.buscar_plano_painel_serializado = AsyncMock(return_value=None)

    app.dependency_overrides[get_atualizar_subtarefa_plano_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    subtarefa = uuid.uuid4()
    response = client.patch(
        f"/diagnosticos/{d_snap.id}/plano-subtarefas/{subtarefa}",
        json={"titulo": "Atualizado"},
        headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
    )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(d_snap.id)
    mock_uc.execute.assert_awaited_once()
