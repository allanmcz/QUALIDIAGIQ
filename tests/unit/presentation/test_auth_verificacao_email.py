"""Testes dos endpoints públicos de verificação de e-mail por OTP."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.email_verificacao import codigo_store
from src.presentation.api.dependencies import get_email_service
from src.presentation.api.main import app


@pytest.fixture(autouse=True)
def _limpar_codigo_store():
    codigo_store.limpar_para_testes()
    yield
    codigo_store.limpar_para_testes()


@pytest.fixture
def client_smtp_ok():
    mock = AsyncMock()
    mock.enviar_codigo_verificacao_email.return_value = True
    app.dependency_overrides[get_email_service] = lambda: mock
    yield TestClient(app)
    app.dependency_overrides.pop(get_email_service, None)


def test_solicitar_verificacao_email_sucesso(client_smtp_ok: TestClient):
    res = client_smtp_ok.post(
        "/auth/verificar-email/solicitar",
        json={"email": "lead@empresa.com.br"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "mensagem" in body
    assert "10" in body["mensagem"] or "minutos" in body["mensagem"].lower()


def test_confirmar_codigo_invalido(client_smtp_ok: TestClient):
    client_smtp_ok.post("/auth/verificar-email/solicitar", json={"email": "x@y.z"})
    codigo = codigo_store.codigo_ativo_para_debug("x@y.z")
    assert codigo is not None
    res = client_smtp_ok.post(
        "/auth/verificar-email/confirmar",
        json={"email": "x@y.z", "codigo": "000000"},
    )
    assert res.status_code == 400


def test_confirmar_codigo_valido(client_smtp_ok: TestClient):
    client_smtp_ok.post("/auth/verificar-email/solicitar", json={"email": "ok@teste.com"})
    codigo = codigo_store.codigo_ativo_para_debug("ok@teste.com")
    assert codigo is not None
    res = client_smtp_ok.post(
        "/auth/verificar-email/confirmar",
        json={"email": "ok@teste.com", "codigo": codigo},
    )
    assert res.status_code == 200
    assert res.json() == {"verificado": True}


def test_self_service_token_codigo_valido(client_smtp_ok: TestClient):
    client_smtp_ok.post("/auth/verificar-email/solicitar", json={"email": "self@svc.br"})
    codigo = codigo_store.codigo_ativo_para_debug("self@svc.br")
    assert codigo is not None
    res = client_smtp_ok.post(
        "/auth/self-service/token",
        json={"email": "self@svc.br", "codigo": codigo},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body.get("token_type") == "bearer"
    assert int(body.get("expires_in", 0)) > 0


def test_self_service_token_codigo_invalido(client_smtp_ok: TestClient):
    client_smtp_ok.post("/auth/verificar-email/solicitar", json={"email": "bad@svc.br"})
    res = client_smtp_ok.post(
        "/auth/self-service/token",
        json={"email": "bad@svc.br", "codigo": "000000"},
    )
    assert res.status_code == 400


def test_solicitar_falha_smtp_nao_registra_codigo():
    mock = AsyncMock()
    mock.enviar_codigo_verificacao_email.return_value = False
    app.dependency_overrides[get_email_service] = lambda: mock
    try:
        client = TestClient(app)
        res = client.post("/auth/verificar-email/solicitar", json={"email": "fail@smtp.br"})
        assert res.status_code == 503
        assert codigo_store.codigo_ativo_para_debug("fail@smtp.br") is None
    finally:
        app.dependency_overrides.pop(get_email_service, None)
