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

    def test_pode_reenviar_false_antes_intervalo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ramo quando último envio foi há menos de ``_RATE_SEGUNDOS`` segundos."""
        em = codigo_store.normalizar_email("cooldown@test.br")
        with codigo_store._lock:
            codigo_store._ultimo_envio[em] = 1_000_000.0
        monkeypatch.setattr(
            "src.infrastructure.email_verificacao.codigo_store.time.monotonic",
            lambda: 1_000_000.0 + 10.0,
        )
        assert codigo_store.pode_reenviar(em) is False

    def test_pode_reenviar_true_apos_intervalo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        em = codigo_store.normalizar_email("liberado@test.br")
        with codigo_store._lock:
            codigo_store._ultimo_envio[em] = 1_000_000.0
        monkeypatch.setattr(
            "src.infrastructure.email_verificacao.codigo_store.time.monotonic",
            lambda: 1_000_000.0 + 50.0,
        )
        assert codigo_store.pode_reenviar(em) is True
