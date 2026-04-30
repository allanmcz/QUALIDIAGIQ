from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import ScoreCompleto


class PdfGeneratorPort(ABC):
    """
    Porta (Interface) para a geração de relatórios PDF.
    
    Camada: Application
    """
    
    @abstractmethod
    async def gerar_pdf_diagnostico(
        self, diagnostico: Diagnostico, score: ScoreCompleto, recomendacao_ia: str | None = None
    ) -> bytes:
        """
        Gera um PDF a partir dos dados do diagnóstico e score.
        Retorna os bytes do arquivo gerado.
        """
        pass
