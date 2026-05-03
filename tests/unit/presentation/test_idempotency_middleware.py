"""Testes do middleware de idempotência (POST /diagnosticos/)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_auth_bearer

client = TestClient(app)

_PAYLOAD_BASE = {
    "empresa": {
        "cnpj": "12345678000195",
        "razao_social": "Empresa Idem LTDA",
        "porte": "micro",
        "regime": "simples_nacional",
        "cnae_principal": "1234567",
        "uf": "SP",
        "setor_macro": "comercio",
    },
    "respondente": {"email": "teste@teste.com"},
    "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
    "aceite_termos_privacidade": True,
}


def _mock_use_case_sucesso() -> AsyncMock:
    mock_use_case = AsyncMock()
    mock_resultado = MagicMock()
    mock_resultado.diagnostico.id = uuid.uuid4()
    mock_resultado.diagnostico.status.value = "finalizado"
    mock_resultado.diagnostico.plano.value = "gratuito"
    mock_resultado.diagnostico.empresa.razao_social = "Empresa Idem LTDA"
    mock_resultado.diagnostico.empresa.faixa_faturamento = None
    mock_resultado.score.score_geral.valor = 88.0
    mock_resultado.score.score_geral.peso_total_aplicado = 1.0
    dimensao_mock = MagicMock()
    dimensao_mock.valor = 88.0
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
    mock_resultado.diagnostico.versao_otimista = 1
    mock_resultado.diagnostico.aceite_termos_privacidade_em = datetime.now(UTC)
    mock_resultado.diagnostico.locale_relatorio = "pt-BR"
    mock_use_case.execute.return_value = mock_resultado
    return mock_use_case


def test_post_diagnostico_sem_idempotency_key_retorna_400() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: _mock_use_case_sucesso()

    try:
        r = client.post(
            "/diagnosticos/",
            json=_PAYLOAD_BASE,
            headers=cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        )
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 400
    assert "Idempotency-Key" in r.json()["detail"]


def test_post_diagnostico_replay_retorna_header_e_nao_reexecuta_use_case() -> None:
    """Mesma chave + mesmo Authorization → resposta cacheada (previsibilidade operacional)."""
    mock_uc = _mock_use_case_sucesso()
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    idem = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    headers = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": idem,
    }

    try:
        r1 = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers)
        assert r1.status_code == 201
        assert r1.headers.get("X-Idempotent-Replay") is None

        r2 = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers)
        assert r2.status_code == 201
        assert r2.headers.get("X-Idempotent-Replay") == "true"
        assert r2.json() == r1.json()
    finally:
        app.dependency_overrides.clear()

    assert mock_uc.execute.call_count == 1


def test_post_diagnostico_mesma_chave_tenant_diferente_executa_duas_vezes() -> None:
    """Chave composta inclui Authorization — tenant distinto não deve receber replay alheio."""
    mock_uc_a = _mock_use_case_sucesso()
    mock_uc_b = _mock_use_case_sucesso()
    tid_a = uuid.uuid4()
    tid_b = uuid.uuid4()
    uid = uuid.uuid4()
    idem = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc_a
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid_a, "gratuito")
    headers_a = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid_a),
        "Idempotency-Key": idem,
    }

    try:
        r_a = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers_a)
        assert r_a.status_code == 201
        assert r_a.headers.get("X-Idempotent-Replay") is None
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc_b
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid_b, "gratuito")
    headers_b = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid_b),
        "Idempotency-Key": idem,
    }

    try:
        r_b = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers_b)
        assert r_b.status_code == 201
        assert r_b.headers.get("X-Idempotent-Replay") is None
    finally:
        app.dependency_overrides.clear()

    assert mock_uc_a.execute.call_count == 1
    assert mock_uc_b.execute.call_count == 1


def test_post_diagnostico_chaves_idempotencia_distintas_executa_duas_vezes() -> None:
    """Duas chaves distintas no mesmo tenant → use case executado duas vezes (sem replay)."""
    mock_uc = _mock_use_case_sucesso()
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    h1 = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": "11111111-1111-1111-1111-111111111111",
    }
    h2 = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": "22222222-2222-2222-2222-222222222222",
    }

    try:
        r1 = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=h1)
        r2 = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=h2)
    finally:
        app.dependency_overrides.clear()

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.headers.get("X-Idempotent-Replay") is None
    assert r2.headers.get("X-Idempotent-Replay") is None
    assert mock_uc.execute.call_count == 2
