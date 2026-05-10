"""Testes HTTP — ``POST /referencia/cnpj/consulta_cnpj`` com dependências sobrescritas."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.application.services.cnpj_consulta_service import ConsultaCnpjMaterializada
from src.presentation.api.dependencies import get_consultar_cnpj_use_case, get_current_user_tenant
from src.presentation.api.main import app
from src.presentation.api.routers.cnpj_router import consultar_cnpj
from src.presentation.api.schemas import ConsultarCnpjRequest
from tests.conftest import cabecalho_auth_bearer

client = TestClient(app)
CNPJ_OK = "33014556000196"


@pytest.mark.asyncio
async def test_consultar_cnpj_idempotency_none_normaliza_vazio() -> None:
    """Chamada direta com ``None`` cobre ``(idempotency_key or \"\")`` (sem header FastAPI)."""
    req = MagicMock()
    req.state = MagicMock(spec=["trace_id"], trace_id=None)
    body = ConsultarCnpjRequest.model_validate(
        {"cnpj": CNPJ_OK, "force_refresh": False, "aplicar_no_diagnostico_id": None}
    )
    mock_uc = MagicMock()
    with pytest.raises(HTTPException) as exc:
        await consultar_cnpj(
            req,
            body,
            (uuid4(), uuid4(), "gratuito"),
            mock_uc,
            None,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 400
    mock_uc.executar_e_materializar.assert_not_called()


def test_consultar_cnpj_rejeita_idempotency_vazio() -> None:
    uid = uuid4()
    tid = uuid4()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "   ",
            },
            json={"cnpj": CNPJ_OK},
        )
        assert res.status_code == 400
        assert "Idempotency" in str(res.json().get("detail", ""))
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)


def test_consultar_cnpj_rejeita_idempotency_string_vazio_explicito() -> None:
    """Header presente mas vazio após ``strip`` ⇒ 400 (paridade com apenas espaços)."""
    uid = uuid4()
    tid = uuid4()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "",
            },
            json={"cnpj": CNPJ_OK},
        )
        assert res.status_code == 400
        assert "Idempotency" in str(res.json().get("detail", ""))
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)


def test_consultar_cnpj_valor_erro_bad_request() -> None:
    uid = uuid4()
    tid = uuid4()
    mock_uc = MagicMock()
    mock_uc.executar_e_materializar = AsyncMock(
        side_effect=ValueError("CNPJ já liquidado fictício")
    )

    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_consultar_cnpj_use_case] = lambda: mock_uc
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "idem-vl",
            },
            json={"cnpj": CNPJ_OK},
        )
        assert res.status_code == 400
        assert "liquidado" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)
        app.dependency_overrides.pop(get_consultar_cnpj_use_case, None)


def test_consultar_cnpj_runtime_erro_servico_indisponivel() -> None:
    uid = uuid4()
    tid = uuid4()
    mock_uc = MagicMock()
    mock_uc.executar_e_materializar = AsyncMock(
        side_effect=RuntimeError("fonte externa indisponível")
    )

    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_consultar_cnpj_use_case] = lambda: mock_uc
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "idem-rt",
            },
            json={"cnpj": CNPJ_OK},
        )
        assert res.status_code == 503
        assert "indisponível" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)
        app.dependency_overrides.pop(get_consultar_cnpj_use_case, None)


def test_consultar_cnpj_sucesso_e_canonico() -> None:
    uid = uuid4()
    tid = uuid4()
    exp = datetime.now(UTC)
    cid = uuid4()
    canon = {
        "cnpj": CNPJ_OK,
        "razao_social": "Firma QA",
        "nome_fantasia": " ",
        "cnae_principal": "4712100",
        "porte": "medio",
    }
    mat = ConsultaCnpjMaterializada(
        consulta_id=cid,
        cnpj_14=CNPJ_OK,
        payload_bruto={"x": 1},
        payload_canonico=canon,
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    mock_uc = MagicMock()
    mock_uc.executar_e_materializar = AsyncMock(return_value=(mat, False))

    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_consultar_cnpj_use_case] = lambda: mock_uc
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "idem-ok",
            },
            json={"cnpj": CNPJ_OK, "force_refresh": True},
        )
        assert res.status_code == 200
        j = res.json()
        assert j["consulta_id"] == str(cid)
        assert j["cnpj"] == CNPJ_OK
        assert j["fonte"] == "brasil_api"
        assert j["canonico"]["razao_social"] == "Firma QA"
        assert j["canonico"]["nome_fantasia"] is None
        assert j["canonico"]["cnae_principal"] == "4712100"

        kw = mock_uc.executar_e_materializar.await_args.args[0]
        assert isinstance(kw.trace_id, str) and len(kw.trace_id.strip()) >= 8
        assert kw.force_refresh is True
        assert kw.idempotency_key == "idem-ok"
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)
        app.dependency_overrides.pop(get_consultar_cnpj_use_case, None)


def test_consultar_cnpj_repasse_header_x_trace_id() -> None:
    """Middleware de trace propaga ``X-Trace-Id`` — a rota passa ao use case."""
    uid = uuid4()
    tid = uuid4()
    exp = datetime.now(UTC)
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14=CNPJ_OK,
        payload_bruto={},
        payload_canonico={"cnpj": CNPJ_OK},
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    mock_uc = MagicMock()
    mock_uc.executar_e_materializar = AsyncMock(return_value=(mat, False))

    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_consultar_cnpj_use_case] = lambda: mock_uc

    esperado = "correlacao-fixa-trace-id"
    try:
        res = client.post(
            "/referencia/cnpj/consulta_cnpj",
            headers={
                **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
                "Idempotency-Key": "idem-tr",
                "X-Trace-Id": esperado,
            },
            json={"cnpj": CNPJ_OK},
        )
        assert res.status_code == 200
        cmd = mock_uc.executar_e_materializar.await_args.args[0]
        assert cmd.trace_id == esperado
    finally:
        app.dependency_overrides.pop(get_current_user_tenant, None)
        app.dependency_overrides.pop(get_consultar_cnpj_use_case, None)
