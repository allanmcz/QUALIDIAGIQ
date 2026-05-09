"""Testes do middleware de idempotência (POST /diagnosticos/)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cachetools import TTLCache
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.datastructures import MutableHeaders
from starlette.requests import Request

from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.main import app
from src.presentation.api.middleware.idempotency import IdempotencyMiddleware
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
    "respondente": {"email": "teste@teste.com", "nome": "Respondente QA"},
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
    mock_resultado.diagnostico.relatorio_pdf_url = None
    mock_resultado.diagnostico.score_completo_snapshot = ScoreCompleto(
        score_geral=ScoreNumerico(valor=88.0, peso_total_aplicado=1.0),
        score_por_dimensao={
            Dimensao.FISCAL: ScoreNumerico(valor=88.0, peso_total_aplicado=1.0),
        },
    )
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
        # Não usar ``clear()`` — remove o mock de ``get_diagnostico_repository`` do conftest
        # e o segundo POST instanciaria Supabase real na mesma função de teste.
        app.dependency_overrides.pop(get_realizar_diagnostico_use_case, None)
        app.dependency_overrides.pop(get_current_user_tenant, None)

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


def test_post_diagnostico_idempotency_key_muito_longa_400() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: _mock_use_case_sucesso()

    idem_ok = "a" * 128
    idem_bad = "b" * 129
    h_ok = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": idem_ok,
    }
    h_bad = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": idem_bad,
    }

    try:
        r_bad = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=h_bad)
        assert r_bad.status_code == 400
        assert "128" in r_bad.json().get("detail", "")

        r_ok = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=h_ok)
        assert r_ok.status_code == 201
    finally:
        app.dependency_overrides.clear()


def test_post_diagnostico_aceita_header_idempotency_key_minusculo() -> None:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: _mock_use_case_sucesso()

    headers = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "idempotency-key": "cccccccc-cccc-cccc-cccc-cccccccccccc",
    }

    try:
        r = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers)
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 201


def test_post_diagnostico_replay_via_postgres_engine_curto_circuito() -> None:
    """Com ``app.state.idempotency_engine``, o hit vem de ``idempotency_get`` (thread)."""
    cached = CorpoCacheadoIdempotencia(
        status_code=201,
        body=b'{"ok":true,"id":"00000000-0000-0000-0000-000000000001"}',
        headers=(
            ("content-type", "application/json"),
            ("x-parcelado-teste", "1"),
        ),
    )
    uid = uuid.uuid4()
    tid = uuid.uuid4()

    prev_engine = getattr(app.state, "idempotency_engine", None)
    app.state.idempotency_engine = MagicMock()

    mock_uc = _mock_use_case_sucesso()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    headers = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": "dddddddd-dddd-dddd-dddd-dddddddddddd",
    }

    try:
        with patch(
            "src.infrastructure.idempotency.postgres_backend.idempotency_get",
            return_value=cached,
        ):
            r = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers)
        assert r.status_code == 201
        assert r.headers.get("X-Idempotent-Replay") == "true"
        assert r.json().get("ok") is True
        assert mock_uc.execute.call_count == 0
    finally:
        app.dependency_overrides.clear()
        if prev_engine is None:
            delattr(app.state, "idempotency_engine")
        else:
            app.state.idempotency_engine = prev_engine


def test_get_health_nao_exige_idempotency_key() -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_post_diagnostico_chama_idempotency_put_quando_engine_postgres() -> None:
    """Após 2xx, o middleware persiste o corpo em ``idempotency_put`` (thread síncrona)."""
    mock_put = MagicMock()
    prev_engine = getattr(app.state, "idempotency_engine", None)
    engine_holder = MagicMock()
    app.state.idempotency_engine = engine_holder
    app.state.idempotency_ttl_seconds = 120

    tid = uuid.uuid4()
    uid = uuid.uuid4()
    mock_uc = _mock_use_case_sucesso()
    app.dependency_overrides[get_realizar_diagnostico_use_case] = lambda: mock_uc
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "gratuito")

    headers = {
        **cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid),
        "Idempotency-Key": "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    }

    async def to_thread_eager(fn: object, /, *args: object, **kwargs: object) -> object:
        return fn(*args, **kwargs)

    try:
        with (
            patch(
                "src.infrastructure.idempotency.postgres_backend.idempotency_get",
                return_value=None,
            ),
            patch(
                "src.infrastructure.idempotency.postgres_backend.idempotency_put",
                mock_put,
            ),
            patch(
                "src.presentation.api.middleware.idempotency.asyncio.to_thread",
                side_effect=to_thread_eager,
            ),
        ):
            r = client.post("/diagnosticos/", json=_PAYLOAD_BASE, headers=headers)
    finally:
        app.dependency_overrides.clear()
        if prev_engine is None:
            delattr(app.state, "idempotency_engine")
        else:
            app.state.idempotency_engine = prev_engine

    assert r.status_code == 201
    mock_put.assert_called_once()
    args_put = mock_put.call_args[0]
    assert args_put[0] is engine_holder
    assert args_put[3] == 120
    assert args_put[4] == tid


def _starlette_app_sem_engine_postgres() -> Starlette:
    """App mínimo com estado esperado pelo middleware (cache em memória)."""
    app = Starlette()
    app.state.idempotency_engine = None
    app.state.idempotency_ttl_seconds = 3600
    return app


def _scope_post_diagnosticos(
    starlette_app: Starlette,
    header_pairs: list[tuple[bytes, bytes]],
    *,
    client_host: tuple[str, int] | None = ("127.0.0.1", 3333),
) -> dict[str, object]:
    scope: dict[str, object] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": "/diagnosticos/",
        "raw_path": b"/diagnosticos/",
        "query_string": b"",
        "headers": header_pairs,
        "scheme": "http",
        "server": ("test", 80),
        "app": starlette_app,
    }
    if client_host is not None:
        scope["client"] = client_host
    return scope


@pytest.mark.asyncio
async def test_dispatch_extrai_corpo_via_body_quando_sem_body_iterator() -> None:
    """Resposta sem ``body_iterator`` (objeto legado) deve usar ``body`` — ramo else."""
    inner = _starlette_app_sem_engine_postgres()
    cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(maxsize=64, ttl=120)
    mw = IdempotencyMiddleware(inner, cache)
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    auth = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)["Authorization"].encode()
    headers = [
        (b"authorization", auth),
        (b"idempotency-key", b"88888888-8888-8888-8888-888888888888"),
    ]
    scope = _scope_post_diagnosticos(inner, headers)

    class RespostaSoBody:
        """ASGI legado / mock sem iterador — só ``body`` bytes."""

        status_code = 201
        media_type = "application/json"
        body = b'{"via":"body"}'
        headers = MutableHeaders({"content-type": "application/json"})

    async def call_next(_: Request) -> RespostaSoBody:
        return RespostaSoBody()

    async def receive() -> dict[str, object]:  # pragma: no cover — ASGI mínimo
        return {"type": "http.disconnect"}

    req = Request(scope, receive)
    resp = await mw.dispatch(req, call_next)
    assert resp.status_code == 201
    assert resp.body == b'{"via":"body"}'


@pytest.mark.asyncio
async def test_dispatch_corpo_nao_bytes_converte_bytes() -> None:
    """``body`` não-``bytes`` (ex.: ``bytearray``) deve passar por ``bytes(raw)``."""
    inner = _starlette_app_sem_engine_postgres()
    cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(maxsize=64, ttl=120)
    mw = IdempotencyMiddleware(inner, cache)
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    auth = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)["Authorization"].encode()
    headers = [
        (b"authorization", auth),
        (b"idempotency-key", b"77777777-7777-7777-7777-777777777777"),
    ]
    scope = _scope_post_diagnosticos(inner, headers)

    class RespostaBytearray:
        status_code = 200
        media_type = "application/json"
        body = bytearray(b'{"bb":1}')
        headers = MutableHeaders({"content-type": "application/json"})

    async def call_next(_: Request) -> RespostaBytearray:
        return RespostaBytearray()

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(scope, receive)
    resp = await mw.dispatch(req, call_next)
    assert resp.body == b'{"bb":1}'


@pytest.mark.asyncio
async def test_dispatch_agrega_chunks_do_body_iterator() -> None:
    """Ramo ``async for`` sobre ``body_iterator`` (resposta streaming típica)."""
    inner = _starlette_app_sem_engine_postgres()
    cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(maxsize=64, ttl=120)
    mw = IdempotencyMiddleware(inner, cache)
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    auth = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)["Authorization"].encode()
    headers = [
        (b"authorization", auth),
        (b"idempotency-key", b"66666666-6666-6666-6666-666666666666"),
    ]
    scope = _scope_post_diagnosticos(inner, headers)

    class RespostaChunked:
        status_code = 201
        media_type = "application/json"
        headers = MutableHeaders({"content-type": "application/json"})

        def __init__(self) -> None:
            async def _gen() -> object:
                yield b'{"st":'
                yield b'"ok"}'

            self.body_iterator = _gen()

    async def call_next(_: Request) -> RespostaChunked:
        return RespostaChunked()

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(scope, receive)
    resp = await mw.dispatch(req, call_next)
    assert resp.body == b'{"st":"ok"}'


@pytest.mark.asyncio
async def test_dispatch_body_iterator_sem_chunks_corpo_vazio() -> None:
    """Iterador presente mas sem iterações — cobre saída imediata do ``async for``."""
    inner = _starlette_app_sem_engine_postgres()
    cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(maxsize=64, ttl=120)
    mw = IdempotencyMiddleware(inner, cache)
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    auth = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)["Authorization"].encode()
    headers = [
        (b"authorization", auth),
        (b"idempotency-key", b"44444444-4444-4444-4444-444444444444"),
    ]
    scope = _scope_post_diagnosticos(inner, headers)

    class RespostaIteratorVazio:
        status_code = 200
        media_type = "application/json"
        headers = MutableHeaders({"content-type": "application/json"})

        def __init__(self) -> None:
            async def _sem_chunks() -> None:
                if False:  # pragma: no cover — mantém generator assíncrono vazio
                    yield b""

            self.body_iterator = _sem_chunks()

    async def call_next(_: Request) -> RespostaIteratorVazio:
        return RespostaIteratorVazio()

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(scope, receive)
    resp = await mw.dispatch(req, call_next)
    assert resp.body == b""


@pytest.mark.asyncio
async def test_dispatch_sem_body_nem_iterator_corpo_vazio() -> None:
    """``body_iterator`` ausente e ``body`` None → corpo permanece vazio (limite)."""
    inner = _starlette_app_sem_engine_postgres()
    cache: TTLCache[str, CorpoCacheadoIdempotencia] = TTLCache(maxsize=64, ttl=120)
    mw = IdempotencyMiddleware(inner, cache)
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    auth = cabecalho_auth_bearer(usuario_id=uid, tenant_id=tid)["Authorization"].encode()
    headers = [
        (b"authorization", auth),
        (b"idempotency-key", b"55555555-5555-5555-5555-555555555555"),
    ]
    scope = _scope_post_diagnosticos(inner, headers)

    class RespostaVazia:
        status_code = 204
        media_type = None
        body = None
        headers = MutableHeaders()

    async def call_next(_: Request) -> RespostaVazia:
        return RespostaVazia()

    async def receive() -> dict[str, object]:  # pragma: no cover
        return {"type": "http.disconnect"}

    req = Request(scope, receive)
    resp = await mw.dispatch(req, call_next)
    assert resp.body == b""
