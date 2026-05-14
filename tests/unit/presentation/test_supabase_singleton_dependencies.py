"""Cobertura do singleton ``get_supabase_client`` (memoização por processo)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.infrastructure.config.settings import get_settings
from src.presentation.api import dependencies as deps
from src.presentation.api import deps_auth_supabase


def test_supabase_singleton_reutiliza_instancia_entre_chamadas() -> None:
    get_settings.cache_clear()
    deps_auth_supabase.reset_supabase_client_singleton()

    fake_cli = MagicMock()

    m = MagicMock()
    m.supabase_url = "http://localhost:54321"
    m.supabase_key = "svc-key-xx"

    try:
        with (
            patch("src.presentation.api.deps_auth_supabase.get_settings", return_value=m),
            patch(
                "src.presentation.api.deps_auth_supabase.create_client",
                return_value=fake_cli,
            ) as mock_create,
        ):
            a = deps.get_supabase_client()
            b = deps.get_supabase_client()
        assert a is fake_cli is b
        mock_create.assert_called_once_with("http://localhost:54321", "svc-key-xx")
    finally:
        deps_auth_supabase.reset_supabase_client_singleton()
        get_settings.cache_clear()
