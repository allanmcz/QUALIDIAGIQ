"""Testes do adaptador SMTP com ``smtplib`` mockado (sem rede real)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.adapters.email_smtp import SmtpEmailAdapter


@pytest.mark.asyncio
async def test_enviar_codigo_smtp_sem_auth_retorna_true() -> None:
    adapter = SmtpEmailAdapter()
    adapter.smtp_host = "127.0.0.42"
    adapter.smtp_port = 10250
    adapter.smtp_user = ""
    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.return_value = mock_smtp_inst
    mock_smtp_inst.__exit__.return_value = None

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_codigo_verificacao_email("a@test.io", "123456", 10)
    assert ok is True
    mock_smtp_inst.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_enviar_codigo_com_starttls_login_quando_credenciais(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMTP_USER", "usr")
    monkeypatch.setenv("SMTP_PASS", "sec")
    adapter = SmtpEmailAdapter()
    adapter.smtp_host = "smtp.test"
    adapter.smtp_port = 587

    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.return_value = mock_smtp_inst
    mock_smtp_inst.__exit__.return_value = None

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_codigo_verificacao_email("lead@test.io", "000111", 5)
    assert ok is True
    mock_smtp_inst.starttls.assert_called_once()
    mock_smtp_inst.login.assert_called_once_with("usr", "sec")
    mock_smtp_inst.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_enviar_codigo_retorna_false_em_excecao() -> None:
    adapter = SmtpEmailAdapter()
    adapter.smtp_host = "127.0.0.1"

    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.side_effect = OSError("porta recusada")

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_codigo_verificacao_email("z@test.io", "999999", 10)
    assert ok is False


@pytest.mark.asyncio
async def test_enviar_relatorio_pdf_retorna_true() -> None:
    adapter = SmtpEmailAdapter()
    adapter.smtp_user = ""
    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.return_value = mock_smtp_inst
    mock_smtp_inst.__exit__.return_value = None

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_email_com_relatorio(
            destinatario_email="ceo@empresa.com",
            destinatario_nome="Maria",
            pdf_url="https://blob/x.pdf",
        )
    assert ok is True
    mock_smtp_inst.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_enviar_relatorio_retorna_false_quando_erro_interno() -> None:
    adapter = SmtpEmailAdapter()
    adapter.smtp_user = ""
    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.side_effect = TimeoutError()

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_email_com_relatorio("a@b.c", "A", "https://z")
    assert ok is False


@pytest.mark.asyncio
async def test_enviar_relatorio_com_starttls_login_quando_credenciais(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SMTP_USER", "usr")
    monkeypatch.setenv("SMTP_PASS", "sec")
    adapter = SmtpEmailAdapter()
    adapter.smtp_host = "smtp.example.org"
    adapter.smtp_port = 587

    mock_smtp_inst = MagicMock()
    mock_smtp_inst.__enter__.return_value = mock_smtp_inst
    mock_smtp_inst.__exit__.return_value = None

    with patch("src.infrastructure.adapters.email_smtp.smtplib.SMTP", return_value=mock_smtp_inst):
        ok = await adapter.enviar_email_com_relatorio("lead@test.io", "Maria", "https://blob/x.pdf")
    assert ok is True
    mock_smtp_inst.starttls.assert_called_once()
    mock_smtp_inst.login.assert_called_once_with("usr", "sec")
    mock_smtp_inst.send_message.assert_called_once()
