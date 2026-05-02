"""Testes dos validadores de produção em Settings (Sprint 11)."""

from __future__ import annotations

import pytest

from src.infrastructure.config.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _limpar_cache_settings() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _base_producao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "k" * 32)
    monkeypatch.setenv("SUPABASE_URL", "https://projeto.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "chave-anon-nao-vazia")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@db.example.com:5432/app")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")


def test_producao_rejeita_jwt_curto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "curto")
    with pytest.raises(ValueError, match="32"):
        Settings()


def test_producao_rejeita_supabase_http(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_producao(monkeypatch)
    monkeypatch.setenv("SUPABASE_URL", "http://inseguro.example.com")
    with pytest.raises(ValueError, match="https://"):
        Settings()


def test_producao_rejeita_supabase_key_vazio(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_producao(monkeypatch)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "")
    with pytest.raises(ValueError, match="vazio"):
        Settings()


def test_producao_exige_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_producao(monkeypatch)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings()


def test_producao_rejeita_smtp_local(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_producao(monkeypatch)
    monkeypatch.setenv("SMTP_HOST", "mailpit")
    with pytest.raises(ValueError, match="mailpit"):
        Settings()


def test_producao_config_valida(monkeypatch: pytest.MonkeyPatch) -> None:
    _base_producao(monkeypatch)
    s = Settings()
    assert s.supabase_url.startswith("https://")
    assert len(s.jwt_secret_key.get_secret_value()) >= 32
