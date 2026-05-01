from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.application.ports.pdf_generator import PdfGeneratorPort
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import ScoreCompleto


class WeasyPrintPdfGenerator(PdfGeneratorPort):
    """
    Implementação da porta de geração de PDF usando WeasyPrint e Jinja2.
    """

    def __init__(self, template_dir: str | Path | None = None) -> None:
        if template_dir is None:
            # Assume que a pasta 'templates' está no mesmo diretório deste arquivo
            template_dir = Path(__file__).parent / "templates"

        self.env = Environment(loader=FileSystemLoader(str(template_dir)), autoescape=True)

    async def gerar_pdf_diagnostico(
        self,
        diagnostico: Diagnostico,
        score: ScoreCompleto,
        recomendacao_ia: str | None = None,
    ) -> bytes:
        """
        Renderiza o template HTML e o converte para PDF.
        Executado em memória de forma síncrona/blocking dentro do WeasyPrint
        (em produção com alto volume, ideal seria usar run_in_executor).
        """
        # Carregar template
        template = self.env.get_template("relatorio_base.html")

        # Contexto de renderização
        html_str = template.render(
            diagnostico=diagnostico,
            score=score,
            recomendacao_ia=recomendacao_ia,
        )

        # Gerar PDF binário
        # O Weasyprint pode fazer logs warnings caso falte fontes, vamos suprimir opcionalmente.
        pdf_bytes = HTML(string=html_str).write_pdf()

        return bytes(pdf_bytes)
