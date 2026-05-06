"""Testes do mascaramento PII no Sentry (before_send)."""

from __future__ import annotations

from src.infrastructure.observability.sentry_scrubber import (
    _mascarar_string,
    _scrub_dict,
    scrubber_sentry,
)


class TestMascararString:
    def test_email_eh_mascarado(self) -> None:
        assert _mascarar_string("Erro com user@example.com") == "Erro com [EMAIL_REDACTED]"

    def test_cnpj_eh_mascarado(self) -> None:
        assert "[CNPJ_REDACTED]" in _mascarar_string("CNPJ 12.345.678/0001-90 inválido")

    def test_cpf_eh_mascarado(self) -> None:
        assert "[CPF_REDACTED]" in _mascarar_string("CPF 123.456.789-00 conferir")

    def test_telefone_eh_mascarado(self) -> None:
        assert "[TEL_REDACTED]" in _mascarar_string("Liguei para (11) 98765-4321 mas")


class TestScrubDict:
    def test_password_eh_redatado(self) -> None:
        out = _scrub_dict({"username": "joao", "password": "secret123"})
        assert out == {"username": "joao", "password": "[REDACTED]"}

    def test_email_em_valor_string_eh_mascarado(self) -> None:
        out = _scrub_dict({"observacao": "user@example.com tentou login"})
        assert out is not None
        assert "[EMAIL_REDACTED]" in str(out["observacao"])

    def test_recursao_em_dict_aninhado(self) -> None:
        out = _scrub_dict({"req": {"body": {"password": "x"}}})
        assert out is not None
        assert out["req"]["body"]["password"] == "[REDACTED]"


class TestScrubberSentry:
    def test_authorization_header_eh_redatado(self) -> None:
        event = {"request": {"headers": {"Authorization": "Bearer xyz"}}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert scrubbed["request"]["headers"]["Authorization"] == "[REDACTED]"

    def test_password_em_request_data_eh_redatado(self) -> None:
        event = {"request": {"data": {"email": "x@y.com", "password": "secret"}}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert scrubbed["request"]["data"]["password"] == "[REDACTED]"

    def test_user_email_eh_redatado(self) -> None:
        event = {"user": {"id": "uuid-123", "email": "x@y.com"}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert scrubbed["user"]["email"] == "[REDACTED]"
        assert scrubbed["user"]["id"] == "uuid-123"

    def test_exception_message_eh_mascarada(self) -> None:
        event = {"exception": {"values": [{"value": "Falha login para admin@empresa.com"}]}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert "[EMAIL_REDACTED]" in scrubbed["exception"]["values"][0]["value"]

    def test_evento_nao_eh_descartado(self) -> None:
        """Mesmo com PII pesado, o evento DEVE chegar ao Sentry (mascarado)."""
        event = {"message": "Erro genérico"}
        assert scrubber_sentry(event, {}) is not None

    def test_query_string_eh_mascarada(self) -> None:
        event = {"request": {"query_string": "email=a@b.com&x=1"}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert "[EMAIL_REDACTED]" in scrubbed["request"]["query_string"]

    def test_breadcrumb_message_eh_mascarada(self) -> None:
        event = {
            "breadcrumbs": {
                "values": [{"message": "user@empresa.com falhou"}],
            }
        }
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert "[EMAIL_REDACTED]" in scrubbed["breadcrumbs"]["values"][0]["message"]

    def test_extra_dict_eh_scrubado(self) -> None:
        event = {"extra": {"detalhe": "CNPJ 11.222.333/0001-81"}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert "[CNPJ_REDACTED]" in scrubbed["extra"]["detalhe"]

    def test_request_data_string_eh_mascarada(self) -> None:
        event = {"request": {"data": "corpo bruto com x@y.com"}}
        scrubbed = scrubber_sentry(event, {})
        assert scrubbed is not None
        assert scrubbed["request"]["data"] == "corpo bruto com [EMAIL_REDACTED]"
