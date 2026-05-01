"""
Adapter SMTP único para o QDI — envio real de relatório.

Plano ANALISE 11 — Fase A3: não manter mocks SMTP duplicados no repositório; testes/e2e
usam stubs locais onde necessário.
"""

import asyncio
import os
import smtplib
from email.message import EmailMessage

from src.application.ports.email_service import EmailServicePort


class SmtpEmailAdapter(EmailServicePort):
    """Implementação concreta do serviço de e-mail via SMTP padrão."""

    def __init__(self) -> None:
        # Configurações podem vir do ambiente, com fallbacks simulados para MVP
        self.smtp_host = os.environ.get("SMTP_HOST", "localhost")
        self.smtp_port = int(
            os.environ.get("SMTP_PORT", 1025)
        )  # 1025 é porta comum para MailHog/Mailpit
        self.smtp_user = os.environ.get("SMTP_USER", "")
        self.smtp_pass = os.environ.get("SMTP_PASS", "")
        self.sender_email = os.environ.get("SENDER_EMAIL", "no-reply@tributiq.com.br")

    async def enviar_email_com_relatorio(
        self, destinatario_email: str, destinatario_nome: str, pdf_url: str
    ) -> bool:
        """
        Gera e envia o e-mail transacional via SMTP.
        """
        msg = EmailMessage()
        msg["Subject"] = "Seu Diagnóstico QualiDiagIQ está pronto!"
        msg["From"] = self.sender_email
        msg["To"] = destinatario_email

        body = f"""Olá {destinatario_nome},

O seu diagnóstico de maturidade e conformidade tributária foi gerado com sucesso.

Você pode acessá-lo através do link abaixo:
{pdf_url}

Atenciosamente,
Equipe Tributiq
"""
        msg.set_content(body)

        def _send() -> bool:
            try:
                # O timeout de 5 segundos evita que falhas de conexão travem a API muito tempo
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                    if self.smtp_user and self.smtp_pass:
                        server.starttls()
                        server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(msg)
                return True
            except Exception as e:
                import logging

                logging.error(f"Falha ao enviar e-mail via SMTP: {e}")
                return False

        return await asyncio.to_thread(_send)
