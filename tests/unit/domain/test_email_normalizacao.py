"""Testes de ``normalizar_email`` (domain — QDI-H-001)."""

from __future__ import annotations

from src.domain.value_objects.email import normalizar_email


class TestNormalizarEmail:
    """Invariantes da normalização canónica de e-mail."""

    def test_strip_e_lower(self) -> None:
        assert normalizar_email("  User@Test.COM ") == "user@test.com"
