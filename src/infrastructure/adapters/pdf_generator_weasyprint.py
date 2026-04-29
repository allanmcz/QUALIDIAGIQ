import os
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.application.ports.pdf_generator import PdfGeneratorPort
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import ScoreCompleto


class WeasyPrintPdfGenerator(PdfGeneratorPort):
    """
    Implementação concreta do gerador de PDF utilizando WeasyPrint e Jinja2.
    """

    def __init__(self, templates_dir: str | Path | None = None) -> None:
        if templates_dir is None:
            # Caminho relativo seguro até a pasta templates
            base_path = Path(__file__).parent.parent
            self.templates_dir = base_path / "templates"
        else:
            self.templates_dir = Path(templates_dir)

        self.jinja_env = Environment(loader=FileSystemLoader(self.templates_dir), autoescape=True)

    async def gerar_pdf_diagnostico(
        self, diagnostico: Diagnostico, score: ScoreCompleto
    ) -> bytes:
        """
        Renderiza o template jinja com os dados do diagnóstico e coverte para PDF.
        """
        template = self.jinja_env.get_template("relatorio_diagnostico.html")
        
        # Mapeamento de níveis para exibição na UI (ex: badge)
        nivel_mapping = {
            "CRITICO": "Crítico",
            "INICIAL": "Inicial",
            "INTERMEDIARIO": "Intermediário",
            "AVANCADO": "Avançado",
            "EXEMPLAR": "Exemplar"
        }
        
        html_out = template.render(
            diagnostico=diagnostico,
            score_geral=score.score_geral,
            nivel_geral=nivel_mapping.get(score.score_geral.nivel.name, "N/A"),
            dimensoes=score.score_por_dimensao,
            data_geracao=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        )

        css_path = str(self.templates_dir / "style.css")
        
        # WeasyPrint processa o HTML e o CSS
        # Importante: Geração ocorre em thread bloqueante nativa, em prod
        # idealmente encapsulada em asyncio.to_thread, mas aqui WeasyPrint é rápido o suficiente
        # para testes, though wrap for safety
        
        import asyncio
        
        def _render() -> bytes:
            try:
                from weasyprint import CSS, HTML
            except ImportError as e:
                # Caso a biblioteca não consiga carregar no ambiente local devido a dependências OS
                # Isso impede crashs no Mac local sem libpango
                raise RuntimeError(f"Erro ao carregar weasyprint: {e}")
                
            return HTML(string=html_out).write_pdf(stylesheets=[CSS(filename=css_path)]) # type: ignore
            
        pdf_bytes = await asyncio.to_thread(_render)
        return pdf_bytes # type: ignore
