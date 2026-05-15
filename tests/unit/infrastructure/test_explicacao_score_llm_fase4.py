"""Testes ADR-022 Fase 4 — quota, circuit breaker, health, histórico sync, Bedrock stub."""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.domain.ports.llm_gateway import LlmGatewayRequest, LlmTaskType
from src.infrastructure.config.settings import Settings
from src.infrastructure.llm.adapters.bedrock_llm_completer import BedrockLlmCompleter
from src.infrastructure.llm.circuit_breaker import (
    LlmCircuitBreaker,
    get_llm_circuit_breaker,
    reset_llm_circuit_breaker_for_tests,
)
from src.infrastructure.llm.llm_health_probe import probe_llm_health
from src.infrastructure.llm.llm_quota_service import (
    LlmQuotaExcedidaError,
    assert_quota_disponivel_sync,
    contar_uso_llm_hoje_sync,
    registrar_uso_llm_sync,
)
from src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync import (
    inserir_explicacao_score_llm_historico_sync,
    listar_explicacao_score_llm_historico_sync,
)


@pytest.fixture(autouse=True)
def _reset_breaker() -> None:
    reset_llm_circuit_breaker_for_tests()
    yield
    reset_llm_circuit_breaker_for_tests()


class TestLlmCircuitBreaker:
    def test_cooldown_expirado_fecha_circuito(self, monkeypatch: pytest.MonkeyPatch) -> None:
        br = LlmCircuitBreaker(failure_threshold=1, cooldown_seconds=0.01)
        t = [0.0, 0.0, 100.0]

        def mono() -> float:
            return t.pop(0) if t else 100.0

        monkeypatch.setattr(
            "src.infrastructure.llm.circuit_breaker.time.monotonic",
            mono,
        )
        br.record_failure("p")
        assert br.is_open("p") is True
        assert br.is_open("p") is False

    def test_abre_apos_threshold(self) -> None:
        br = LlmCircuitBreaker(failure_threshold=2, cooldown_seconds=3600.0)
        br.record_failure("ollama")
        assert br.is_open("ollama") is False
        br.record_failure("ollama")
        assert br.is_open("ollama") is True

    def test_sucesso_reseta(self) -> None:
        br = LlmCircuitBreaker(failure_threshold=1, cooldown_seconds=3600.0)
        br.record_failure("x")
        assert br.is_open("x") is True
        br.record_success("x")
        assert br.is_open("x") is False

    def test_singleton(self) -> None:
        assert get_llm_circuit_breaker() is get_llm_circuit_breaker()


class TestLlmQuotaService:
    def test_limite_zero_nao_levanta(self) -> None:
        assert_quota_disponivel_sync(
            "postgresql://x",
            tenant_id=uuid.uuid4(),
            task_type="explicacao_score",
            limite_diario=0,
        )

    @patch(
        "src.infrastructure.llm.llm_quota_service.contar_uso_llm_hoje_sync",
        return_value=1,
    )
    def test_quota_disponivel_quando_abaixo_limite(self, _mock_count: MagicMock) -> None:
        assert_quota_disponivel_sync(
            "postgresql://x",
            tenant_id=uuid.uuid4(),
            task_type="explicacao_score",
            limite_diario=50,
        )

    @patch(
        "src.infrastructure.llm.llm_quota_service.contar_uso_llm_hoje_sync",
        return_value=50,
    )
    def test_quota_excedida(self, _mock_count: MagicMock) -> None:
        with pytest.raises(LlmQuotaExcedidaError):
            assert_quota_disponivel_sync(
                "postgresql://x",
                tenant_id=uuid.uuid4(),
                task_type="explicacao_score",
                limite_diario=50,
            )

    def test_registrar_e_contar_com_mock_psycopg2(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = (3,)
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.infrastructure.llm.llm_quota_service.psycopg2.connect",
            lambda _dsn: conn,
        )
        tid = uuid.uuid4()
        registrar_uso_llm_sync("dsn", tenant_id=tid, task_type="explicacao_score", trace_id="t1")
        conn.commit.assert_called()
        n = contar_uso_llm_hoje_sync("dsn", tenant_id=tid, task_type="explicacao_score")
        assert n == 3

    def test_registrar_rollback_em_erro(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("db down")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.infrastructure.llm.llm_quota_service.psycopg2.connect",
            lambda _dsn: conn,
        )
        with pytest.raises(RuntimeError, match="db down"):
            registrar_uso_llm_sync("dsn", tenant_id=uuid.uuid4(), task_type="x")
        conn.rollback.assert_called()


class TestHistoricoSync:
    def _patch_conn(
        self, monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]] | None = None
    ) -> MagicMock:
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.return_value = rows or []
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync.psycopg2.connect",
            lambda _dsn: conn,
        )
        return conn

    def test_inserir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = self._patch_conn(monkeypatch)
        snap = {"text": "ok", "provider": "fake"}
        inserir_explicacao_score_llm_historico_sync(
            "dsn",
            tenant_id=uuid.uuid4(),
            diagnostico_id=uuid.uuid4(),
            snapshot=snap,
            actor_user_id=uuid.uuid4(),
            trace_id="tr",
        )
        conn.commit.assert_called()

    def test_inserir_rollback_em_erro(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = MagicMock()
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("insert fail")
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync.psycopg2.connect",
            lambda _dsn: conn,
        )
        with pytest.raises(RuntimeError, match="insert fail"):
            inserir_explicacao_score_llm_historico_sync(
                "dsn",
                tenant_id=uuid.uuid4(),
                diagnostico_id=uuid.uuid4(),
                snapshot={"text": "x"},
                actor_user_id=None,
                trace_id=None,
            )
        conn.rollback.assert_called()

    def test_listar_com_snapshot_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        snap = {"text": "hist"}
        self._patch_conn(
            monkeypatch,
            [
                {
                    "snapshot": json.dumps(snap),
                    "criado_em": "2026-05-15T12:00:00+00:00",
                    "trace_id": "tr",
                    "actor_user_id": None,
                }
            ],
        )
        out = listar_explicacao_score_llm_historico_sync(
            "dsn",
            tenant_id=uuid.uuid4(),
            diagnostico_id=uuid.uuid4(),
            limit=5,
        )
        assert out[0]["text"] == "hist"
        assert out[0]["trace_id"] == "tr"

    def test_listar_ignora_snapshot_invalido(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_conn(monkeypatch, [{"snapshot": 42, "criado_em": None, "trace_id": None}])
        out = listar_explicacao_score_llm_historico_sync(
            "dsn",
            tenant_id=uuid.uuid4(),
            diagnostico_id=uuid.uuid4(),
        )
        assert out == []


def _settings_probe(**kwargs: object) -> Settings:
    base: dict[str, object] = {"llm_router_enabled": True}
    base.update(kwargs)
    return Settings().model_copy(update=base)


class TestLlmHealthProbe:
    def test_router_desligado(self) -> None:
        s = Settings().model_copy(update={"llm_router_enabled": False})
        assert probe_llm_health(s)["status"] == "disabled"

    def test_backend_cloud(self) -> None:
        s = _settings_probe(llm_backend="anthropic")
        assert probe_llm_health(s)["status"] == "ok"

    def test_bedrock_flag(self) -> None:
        s = _settings_probe(llm_backend="ollama", llm_bedrock_enabled=True)
        assert probe_llm_health(s)["backend"] == "bedrock"

    @patch("urllib.request.urlopen")
    def test_ollama_ok(self, mock_urlopen: MagicMock) -> None:
        resp = MagicMock()
        resp.status = 200
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        s = _settings_probe(llm_backend="ollama")
        assert probe_llm_health(s)["status"] == "ok"

    @patch("urllib.request.urlopen", side_effect=OSError("connection refused"))
    def test_ollama_degraded(self, _mock_urlopen: MagicMock) -> None:
        s = _settings_probe(llm_backend="ollama")
        out = probe_llm_health(s)
        assert out["status"] == "degraded"
        assert "error" in out

    @patch("urllib.request.urlopen")
    def test_ollama_status_nao_200(self, mock_urlopen: MagicMock) -> None:
        resp = MagicMock()
        resp.status = 503
        resp.__enter__ = MagicMock(return_value=resp)
        resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = resp
        s = _settings_probe(llm_backend="ollama")
        assert probe_llm_health(s)["status"] == "degraded"


class TestBedrockCompleter:
    @pytest.mark.asyncio
    async def test_disabled(self) -> None:
        c = BedrockLlmCompleter(Settings(llm_bedrock_enabled=False))
        req = LlmGatewayRequest(
            tenant_id=str(uuid.uuid4()),
            trace_id="t",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="bedrock",
            input_data={},
        )
        with pytest.raises(RuntimeError, match="bedrock_disabled"):
            await c.complete(req)

    @pytest.mark.asyncio
    async def test_misconfigured(self) -> None:
        c = BedrockLlmCompleter(
            Settings().model_copy(
                update={
                    "llm_bedrock_enabled": True,
                    "llm_bedrock_region": "",
                    "llm_bedrock_model_id": "",
                }
            )
        )
        req = LlmGatewayRequest(
            tenant_id=str(uuid.uuid4()),
            trace_id="t",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="bedrock",
            input_data={},
        )
        with pytest.raises(RuntimeError, match="bedrock_misconfigured"):
            await c.complete(req)

    @pytest.mark.asyncio
    async def test_boto3_ausente(self) -> None:
        c = BedrockLlmCompleter(
            Settings().model_copy(
                update={
                    "llm_bedrock_enabled": True,
                    "llm_bedrock_region": "us-east-1",
                    "llm_bedrock_model_id": "anthropic.claude",
                }
            )
        )
        req = LlmGatewayRequest(
            tenant_id=str(uuid.uuid4()),
            trace_id="t",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="bedrock",
            input_data={},
        )
        real_import = __import__

        def _import_sem_boto3(name: str, *args: object, **kwargs: object) -> object:
            if name == "boto3":
                raise ImportError("sem boto3")
            return real_import(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=_import_sem_boto3),
            pytest.raises(RuntimeError, match="bedrock_boto3_missing"),
        ):
            await c.complete(req)

    @pytest.mark.asyncio
    async def test_invoke_model_ok(self) -> None:
        body = MagicMock()
        body.read.return_value = json.dumps(
            {"output": {"message": {"content": [{"text": "resposta bedrock"}]}}}
        ).encode()
        client = MagicMock()
        client.invoke_model.return_value = {"body": body}
        fake_boto3 = MagicMock()
        fake_boto3.client.return_value = client
        c = BedrockLlmCompleter(
            Settings().model_copy(
                update={
                    "llm_bedrock_enabled": True,
                    "llm_bedrock_region": "us-east-1",
                    "llm_bedrock_model_id": "model-x",
                }
            )
        )
        req = LlmGatewayRequest(
            tenant_id=str(uuid.uuid4()),
            trace_id="t",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="bedrock",
            input_data={"score": 1},
        )
        with patch.dict("sys.modules", {"boto3": fake_boto3}):
            texto = await c.complete(req)
        assert texto == "resposta bedrock"

    @pytest.mark.asyncio
    async def test_invoke_model_resposta_vazia(self) -> None:
        body = MagicMock()
        body.read.return_value = json.dumps({"output": {"message": {"content": []}}}).encode()
        client = MagicMock()
        client.invoke_model.return_value = {"body": body}
        fake_boto3 = MagicMock()
        fake_boto3.client.return_value = client
        c = BedrockLlmCompleter(
            Settings().model_copy(
                update={
                    "llm_bedrock_enabled": True,
                    "llm_bedrock_region": "us-east-1",
                    "llm_bedrock_model_id": "model-x",
                }
            )
        )
        req = LlmGatewayRequest(
            tenant_id=str(uuid.uuid4()),
            trace_id="t",
            task_type=LlmTaskType.EXPLICACAO_SCORE,
            prompt_key="bedrock",
            input_data={},
        )
        with (
            patch.dict("sys.modules", {"boto3": fake_boto3}),
            pytest.raises(RuntimeError, match="bedrock_empty_response"),
        ):
            await c.complete(req)
