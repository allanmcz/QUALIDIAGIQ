"""Lifespan (engine sync) e flag OpenTelemetry em `main.py`."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.config.settings import get_settings
from src.presentation.api.main import _derive_otlp_metrics_endpoint, _parse_otlp_headers, lifespan


@pytest.fixture
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_lifespan_cria_engine_quando_database_url(
    monkeypatch: pytest.MonkeyPatch,
    clear_settings_cache: None,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:59999/test_qdi")
    get_settings.cache_clear()

    with patch("src.presentation.api.main.create_engine") as mock_ce:
        mock_ce.return_value = MagicMock()
        from src.presentation.api.main import create_app

        app = create_app()
        with TestClient(app):
            pass
        mock_ce.assert_called_once()
        mock_ce.return_value.dispose.assert_called_once()


def test_instrumentar_otel_console_sem_endpoint(
    clear_settings_cache: None,
) -> None:
    """Ramificação ``else``: ConsoleSpanExporter quando não há OTLP endpoint."""
    fake_settings = MagicMock()
    fake_settings.otel_exporter_otlp_endpoint = ""
    fake_settings.otel_exporter_otlp_headers = None
    fake_settings.otel_service_name = "qdi-console-smoke"

    mock_provider = MagicMock()
    processor_cls = MagicMock()

    with (
        patch(
            "opentelemetry.sdk.trace.TracerProvider",
            return_value=mock_provider,
        ),
        patch("opentelemetry.trace.set_tracer_provider") as mock_set,
        patch(
            "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app",
        ) as mock_instr,
        patch(
            "opentelemetry.sdk.trace.export.BatchSpanProcessor",
            processor_cls,
        ),
        patch(
            "opentelemetry.sdk.trace.export.ConsoleSpanExporter",
            return_value=MagicMock(),
        ) as mock_console,
    ):
        from src.presentation.api.main import _instrumentar_otel

        dummy_app = MagicMock()
        _instrumentar_otel(dummy_app, fake_settings)

    mock_console.assert_called_once()
    mock_instr.assert_called_once_with(dummy_app)
    processor_cls.assert_called_once()
    mock_set.assert_called_once_with(mock_provider)


def test_instrumenar_otel_com_otlp_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    clear_settings_cache: None,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4318/v1/traces")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", 'x-api-key="abc"')
    get_settings.cache_clear()

    fake_settings = MagicMock()
    fake_settings.otel_exporter_otlp_endpoint = "http://collector:4318/v1/traces"
    fake_settings.otel_exporter_otlp_headers = 'x-api-key="abc"'
    fake_settings.otel_service_name = "qdi-api-test"

    mock_provider = MagicMock()
    processor_cls = MagicMock()

    with (
        patch(
            "opentelemetry.sdk.trace.TracerProvider",
            return_value=mock_provider,
        ),
        patch("opentelemetry.trace.set_tracer_provider") as mock_set,
        patch(
            "opentelemetry.instrumentation.fastapi.FastAPIInstrumentor.instrument_app",
        ) as mock_instr,
        patch(
            "opentelemetry.sdk.trace.export.BatchSpanProcessor",
            processor_cls,
        ),
        patch(
            "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter",
            return_value=MagicMock(),
        ),
    ):
        from src.presentation.api.main import _instrumentar_otel
        from src.presentation.api.middleware.otel_http_metrics import OtelHttpMetricsMiddleware

        dummy_app = MagicMock()
        _instrumentar_otel(dummy_app, fake_settings)

    mock_instr.assert_called_once_with(dummy_app)
    mock_provider.add_span_processor.assert_called_once()
    processor_cls.assert_called_once()
    mock_set.assert_called_once_with(mock_provider)
    middlewares = [c.args[0] for c in dummy_app.add_middleware.call_args_list]
    assert OtelHttpMetricsMiddleware in middlewares


def test_create_app_chama_otel_quando_flag(
    monkeypatch: pytest.MonkeyPatch,
    clear_settings_cache: None,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("OTEL_TRACING_ENABLED", "true")
    get_settings.cache_clear()

    with patch("src.presentation.api.main._instrumentar_otel") as mock_otel:
        from src.presentation.api.main import create_app

        create_app()
        mock_otel.assert_called_once()


def test_derive_otlp_metrics_endpoint_substitui_traces_por_metrics() -> None:
    assert (
        _derive_otlp_metrics_endpoint("http://collector:4318/v1/traces")
        == "http://collector:4318/v1/metrics"
    )


def test_derive_otlp_metrics_endpoint_base_sem_suffix_adiciona_metrics() -> None:
    assert (
        _derive_otlp_metrics_endpoint("http://collector:4318") == "http://collector:4318/v1/metrics"
    )


def test_derive_otlp_metrics_endpoint_vazio_retorna_none() -> None:
    assert _derive_otlp_metrics_endpoint("") is None


def test_parse_otlp_headers_vazio_retorna_none() -> None:
    assert _parse_otlp_headers("") is None
    assert _parse_otlp_headers("   ") is None


def test_parse_otlp_headers_parseia_pares_csv() -> None:
    headers = _parse_otlp_headers('k=v, token="abc",empty=')
    assert headers is not None
    assert headers.get("k") == "v"
    assert headers.get("token") == "abc"


def test_parse_otlp_headers_ignora_partes_sem_igual_retorna_so_validas() -> None:
    assert _parse_otlp_headers("só-lixo,key=ok") == {"key": "ok"}


def test_parse_otlp_headers_somentes_invalidas_retorna_none() -> None:
    assert _parse_otlp_headers("a,b,c") is None


@pytest.mark.anyio
async def test_lifespan_inicializa_sentry_quando_dsn(
    monkeypatch: pytest.MonkeyPatch,
    clear_settings_cache: None,
) -> None:
    """Se ``sentry_dsn`` estiver preenchido, ``sentry_sdk.init`` deve ser chamado no startup."""

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()

    fake_settings = MagicMock()
    fake_settings.sync_database_url = ""
    fake_settings.sentry_dsn = " https://deadbeef@sentry.ing/1 "
    fake_settings.idempotency_ttl_seconds = 60
    fake_settings.app_env = "development"

    mock_app = MagicMock()
    mock_app.state = MagicMock()

    with (
        patch("src.presentation.api.main.get_settings", return_value=fake_settings),
        patch("src.presentation.api.main.configurar_logging") as mock_log,
        patch("sentry_sdk.init") as mock_sentry_init,
    ):
        async with lifespan(mock_app):
            pass

    mock_log.assert_called_once()
    mock_sentry_init.assert_called_once()
