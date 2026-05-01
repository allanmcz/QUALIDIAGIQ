"""Lifespan (engine sync) e flag OpenTelemetry em `main.py`."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.infrastructure.config.settings import get_settings


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
