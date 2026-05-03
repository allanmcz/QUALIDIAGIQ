"""Roteamento de ``get_diagnostico_repository`` / ``get_lead_diagnostico_vinculo_port`` com DATABASE_URL."""

from __future__ import annotations

import pytest

from src.infrastructure.config.settings import get_settings
from src.infrastructure.diagnosticos.postgres_lead_diagnostico_vinculo import (
    PostgresLeadDiagnosticoVinculoAdapter,
)
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)
from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_lead_diagnostico_vinculo_port,
)


@pytest.fixture
def _settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_diagnostico_repository_e_postgres_com_dsn_asyncpg(
    monkeypatch: pytest.MonkeyPatch,
    _settings_cache: None,
) -> None:
    """Compose/CI: DSN + asyncpg → mesmo repositório SQL direto que login em admins."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@127.0.0.1:5555/testdb")
    monkeypatch.setenv("QDI_CI_PLAYWRIGHT_INTEGRATED", "1")
    get_settings.cache_clear()
    repo = get_diagnostico_repository()
    assert isinstance(repo, PostgresDiagnosticoRepository)


def test_lead_vinculo_e_postgres_com_dsn(
    monkeypatch: pytest.MonkeyPatch,
    _settings_cache: None,
) -> None:
    """OTP self-service: UPDATE na mesma base quando há DSN (paridade com diagnósticos)."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@127.0.0.1:5555/testdb")
    monkeypatch.setenv("QDI_CI_PLAYWRIGHT_INTEGRATED", "1")
    get_settings.cache_clear()
    port = get_lead_diagnostico_vinculo_port()
    assert isinstance(port, PostgresLeadDiagnosticoVinculoAdapter)
