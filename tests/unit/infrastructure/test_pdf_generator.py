from unittest.mock import MagicMock

import pytest

try:
    from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator

    HAS_WEASYPRINT_DEPS = True
except OSError:
    HAS_WEASYPRINT_DEPS = False

pytestmark = pytest.mark.skipif(
    not HAS_WEASYPRINT_DEPS,
    reason="Dependências C do WeasyPrint não instaladas localmente (pango, cairo, etc)",
)


@pytest.mark.asyncio
async def test_gerar_pdf_diagnostico_sucesso():
    # Arrange
    generator = WeasyPrintPdfGenerator()

    mock_diagnostico = MagicMock()
    mock_diagnostico.empresa.razao_social = "Empresa Teste"
    mock_diagnostico.empresa.cnpj = "12345678000199"
    mock_diagnostico.empresa.porte.value = "Microempresa"
    mock_diagnostico.empresa.regime.value = "Simples Nacional"
    mock_diagnostico.empresa.setor_macro.value = "Serviços"
    mock_diagnostico.respondente.nome = "João Teste"

    mock_score = MagicMock()
    mock_score.score_geral.valor = 85.5
    mock_score.score_geral.nivel.value = "Avançado"
    mock_score.score_geral.peso_total_aplicado = 1.0

    # Criar um dict fake usando um mock pra iterar no template
    dim_key = MagicMock()
    dim_key.value = "fiscal"
    sn = MagicMock()
    sn.valor = 90.0
    sn.peso_total_aplicado = 1.0
    mock_score.score_por_dimensao = {dim_key: sn}

    # Act
    pdf_bytes = await generator.gerar_pdf_diagnostico(mock_diagnostico, mock_score)

    # Assert
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # Valida se o cabeçalho PDF está presente
    assert pdf_bytes.startswith(b"%PDF")
