from abc import ABC, abstractmethod


class EmailServicePort(ABC):
    """
    Porta (Interface) para envio de e-mails transacionais (ex: SMTP, SendGrid, AWS SES).

    Camada: Application
    """

    @abstractmethod
    async def enviar_email_com_relatorio(
        self, destinatario_email: str, destinatario_nome: str, pdf_url: str
    ) -> bool:
        """
        Envia o e-mail contendo o link do relatório PDF.

        Args:
            destinatario_email: E-mail do lead/respondente
            destinatario_nome: Nome do lead
            pdf_url: Link público do PDF salvo no Storage

        Returns:
            Booleano indicando se o envio foi bem-sucedido
        """
        pass

    @abstractmethod
    async def enviar_codigo_verificacao_email(
        self, destinatario_email: str, codigo: str, validade_minutos: int
    ) -> bool:
        """
        Envia código numérico para confirmação de posse do e-mail (wizard / LGPD).

        Args:
            destinatario_email: E-mail do respondente.
            codigo: Código gerado pelo servidor (ex.: 6 dígitos).
            validade_minutos: Prazo informado no corpo da mensagem.

        Returns:
            True se o SMTP aceitou o envio.
        """
        pass
