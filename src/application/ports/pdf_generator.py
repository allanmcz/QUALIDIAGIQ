from abc import ABC, abstractmethod

from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import ScoreCompleto


class PdfGeneratorPort(ABC):
    """
    Porta (Interface) para a geração de relatórios PDF.

    Camada: Application
    """

    @abstractmethod
    async def gerar_pdf_diagnostico(
        self,
        diagnostico: Diagnostico,
        score: ScoreCompleto,
        recomendacao_ia: str | None = None,
        explicacao_score_llm_texto: str | None = None,
    ) -> bytes:
        """
        Gera um PDF a partir dos dados do diagnóstico e score.
        Retorna os bytes do arquivo gerado.
        """
        pass

    @abstractmethod
    async def gerar_pdf_questionario_respostas(
        self,
        diagnostico: Diagnostico,
        respostas: list[dict[str, object]],
    ) -> bytes:
        """PDF com espelho pergunta a resposta (questionário materializado)."""
        pass

    @abstractmethod
    async def gerar_pdf_comparacao_questionario(
        self,
        comparacao: dict[str, object],
        *,
        contexto_diagnostico: Diagnostico,
    ) -> bytes:
        """PDF tabular da comparação entre 2–5 ciclos (mesma empresa)."""
        pass
