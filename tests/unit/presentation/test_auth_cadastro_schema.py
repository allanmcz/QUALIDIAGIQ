"""Validação do schema de cadastro B2B (Pydantic)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.routers.auth_router import CadastroConsultorB2BRequest


class TestCadastroConsultorB2BRequest:
    """Regras mínimas de entrada antes do roteador HTTP."""

    def test_aceita_nome_email_senha_validos(self) -> None:
        m = CadastroConsultorB2BRequest(
            nome="Maria Silva", email="maria@empresa.com", password="12345678"
        )
        assert m.nome == "Maria Silva"
        assert str(m.email) == "maria@empresa.com"

    def test_rejeita_senha_curta(self) -> None:
        with pytest.raises(ValidationError):
            CadastroConsultorB2BRequest(nome="A", email="a@b.com", password="1234567")

    def test_rejeita_nome_vazio_apos_strip(self) -> None:
        with pytest.raises(ValidationError):
            CadastroConsultorB2BRequest(nome="   ", email="a@b.com", password="12345678")
