"""Testes do armazenamento OTP de e-mail (infraestrutura em processo)."""

import pytest

from src.infrastructure.email_verificacao import codigo_store


@pytest.fixture(autouse=True)
def _limpar_store():
    codigo_store.limpar_para_testes()
    yield
    codigo_store.limpar_para_testes()


class TestCodigoStoreEmail:
    """Invariantes de TTL simulado, comparação segura e uso único."""

    def test_registrar_e_validar_consome_codigo(self):
        email = codigo_store.normalizar_email("  User@Test.COM ")
        assert email == "user@test.com"
        codigo_store.registrar_envio(email, "123456")
        assert codigo_store.validar_e_consumir(email, "123456") is True
        assert codigo_store.validar_e_consumir(email, "123456") is False

    def test_codigo_errado_nao_consome(self):
        email = "a@b.co"
        codigo_store.registrar_envio(email, "111111")
        assert codigo_store.validar_e_consumir(email, "999999") is False
        assert codigo_store.validar_e_consumir(email, "111111") is True

    def test_normalizar_email(self):
        assert codigo_store.normalizar_email(" X@Y.Z ") == "x@y.z"
