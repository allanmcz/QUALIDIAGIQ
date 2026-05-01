import logging

from src.application.ports.email_service import EmailServicePort

logger = logging.getLogger(__name__)


class MockEmailService(EmailServicePort):
    """
    Adapter MOCK para o envio de e-mails.
    Apenas imprime no console ou log o e-mail que seria enviado.
    Ideal para desenvolvimento local sem chaves de SMTP.
    """

    async def enviar_email_com_relatorio(
        self, destinatario_email: str, destinatario_nome: str, pdf_url: str
    ) -> bool:
        """
        Simula o envio do e-mail.
        """
        print(f"\n{'='*50}")
        print("📧 SIMULAÇÃO DE ENVIO DE E-MAIL")
        print(f"Para: {destinatario_nome} <{destinatario_email}>")
        print("Assunto: Seu Diagnóstico QualiDiagIQ está pronto!")
        print(f"\nOlá {destinatario_nome},")
        print(
            "Obrigado por utilizar o QualiDiagIQ. Seu relatório detalhado foi gerado com sucesso."
        )
        print("Acesse o PDF através do link abaixo:")
        print(f"🔗 {pdf_url}")
        print(f"{'='*50}\n")

        logger.info(f"E-mail simulado enviado para {destinatario_email}")

        return True
