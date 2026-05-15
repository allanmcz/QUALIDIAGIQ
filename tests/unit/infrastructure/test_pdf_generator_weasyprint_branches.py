"""Ramos de erro/timeout do ``WeasyPrintPdfGenerator`` — mocks (sem libcairo real)."""

from __future__ import annotations

import asyncio
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator


def _diag_e_score() -> tuple[MagicMock, ScoreCompleto]:
    mock_diagnostico = MagicMock()
    mock_diagnostico.empresa.razao_social = "Empresa Teste"
    mock_diagnostico.empresa.faixa_faturamento = None
    mock_diagnostico.empresa.cnpj = "12345678000195"
    mock_diagnostico.empresa.porte.value = "micro"
    mock_diagnostico.empresa.regime.value = "simples_nacional"
    mock_diagnostico.empresa.setor_macro.value = "servicos"
    mock_diagnostico.respondente.nome = "João"
    mock_diagnostico.respondente.telefone = None
    mock_diagnostico.locale_relatorio = "pt-BR"

    score = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )
    return mock_diagnostico, score


@pytest.mark.asyncio
async def test_init_templates_dir_explicito(tmp_path: object) -> None:
    gen = WeasyPrintPdfGenerator(templates_dir=tmp_path)
    assert gen.templates_dir == tmp_path


@pytest.mark.asyncio
async def test_render_timeout_lanca_runtime_error() -> None:
    gen = WeasyPrintPdfGenerator()
    tpl = MagicMock()
    tpl.render = MagicMock(return_value="<html><body>x</body></html>")
    gen.jinja_env.get_template = MagicMock(return_value=tpl)
    diag, score = _diag_e_score()

    async def fake_wait_for(aw: object, *, timeout: float) -> object:
        # ``wait_for`` recebe o awaitable de ``to_thread``; se não for aguardado, o Python 3.14
        # emite RuntimeWarning. Fechamos a corrotina sem executar o render pesado.
        _ = timeout
        if asyncio.iscoroutine(aw):
            aw.close()
        raise TimeoutError

    with (
        patch(
            "src.infrastructure.adapters.pdf_generator_weasyprint.get_settings",
            return_value=MagicMock(pdf_render_timeout_seconds=30.0),
        ),
        patch("asyncio.wait_for", fake_wait_for),
        pytest.raises(RuntimeError, match="Timeout ao gerar PDF"),
    ):
        await gen.gerar_pdf_diagnostico(diag, score)


@pytest.mark.asyncio
async def test_weasyprint_indisponivel_retorna_pdf_minimo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Força falha no ``HTML.write_pdf`` sem carregar bibliotecas C (stub ``weasyprint``)."""
    fake_wp = types.SimpleNamespace()

    class _HTMLRuim:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        def write_pdf(self, *a: object, **k: object) -> bytes:
            raise RuntimeError("render fictício")

    fake_wp.HTML = _HTMLRuim
    fake_wp.CSS = MagicMock()
    monkeypatch.setitem(sys.modules, "weasyprint", fake_wp)

    gen = WeasyPrintPdfGenerator()
    tpl = MagicMock()
    tpl.render = MagicMock(return_value="<html><body>x</body></html>")
    gen.jinja_env.get_template = MagicMock(return_value=tpl)
    diag, score = _diag_e_score()

    async def to_thread_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
        assert callable(fn)
        return fn(*args, **kwargs)

    with (
        patch(
            "src.infrastructure.adapters.pdf_generator_weasyprint.get_settings",
            return_value=MagicMock(pdf_render_timeout_seconds=60.0),
        ),
        patch.object(asyncio, "to_thread", to_thread_imediato),
    ):
        pdf = await gen.gerar_pdf_diagnostico(diag, score)

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_gerar_pdf_inclui_score_explain_box_quando_texto_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bloco ``score_explain`` do template quando ``explicacao_score_llm_texto`` é informado."""
    html_gerado: list[str] = []
    fake_wp = types.SimpleNamespace()

    class _HTMLCaptura:
        def __init__(self, *, string: str, **kwargs: object) -> None:
            _ = kwargs
            html_gerado.append(string)

        def write_pdf(self, *args: object, **kwargs: object) -> bytes:
            _ = args, kwargs
            return b"%PDF-1.4\n%%EOF"

    fake_wp.HTML = _HTMLCaptura
    fake_wp.CSS = MagicMock()
    monkeypatch.setitem(sys.modules, "weasyprint", fake_wp)

    gen = WeasyPrintPdfGenerator()
    diag, score = _diag_e_score()
    narrativa = "Priorize a dimensão fiscal (LC 214/2025 art. 5º)."

    async def to_thread_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
        assert callable(fn)
        return fn(*args, **kwargs)

    with (
        patch(
            "src.infrastructure.adapters.pdf_generator_weasyprint.get_settings",
            return_value=MagicMock(pdf_render_timeout_seconds=60.0),
        ),
        patch.object(asyncio, "to_thread", to_thread_imediato),
    ):
        await gen.gerar_pdf_diagnostico(
            diag,
            score,
            explicacao_score_llm_texto=narrativa,
        )

    assert len(html_gerado) == 1
    html = html_gerado[0]
    assert "Explicação do score (IA — painel)" in html
    assert narrativa in html
    assert "motor auditável" in html.lower()


@pytest.mark.asyncio
async def test_gerar_pdf_omite_score_explain_box_sem_texto_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sem ``explicacao_score_llm_texto`` o template não renderiza o bloco dedicado."""
    html_gerado: list[str] = []
    fake_wp = types.SimpleNamespace()

    class _HTMLCaptura:
        def __init__(self, *, string: str, **kwargs: object) -> None:
            _ = kwargs
            html_gerado.append(string)

        def write_pdf(self, *args: object, **kwargs: object) -> bytes:
            _ = args, kwargs
            return b"%PDF-1.4\n%%EOF"

    fake_wp.HTML = _HTMLCaptura
    fake_wp.CSS = MagicMock()
    monkeypatch.setitem(sys.modules, "weasyprint", fake_wp)

    gen = WeasyPrintPdfGenerator()
    diag, score = _diag_e_score()

    async def to_thread_imediato(fn: object, /, *args: object, **kwargs: object) -> object:
        assert callable(fn)
        return fn(*args, **kwargs)

    with (
        patch(
            "src.infrastructure.adapters.pdf_generator_weasyprint.get_settings",
            return_value=MagicMock(pdf_render_timeout_seconds=60.0),
        ),
        patch.object(asyncio, "to_thread", to_thread_imediato),
    ):
        await gen.gerar_pdf_diagnostico(diag, score, explicacao_score_llm_texto=None)

    assert len(html_gerado) == 1
    assert "Explicação do score (IA — painel)" not in html_gerado[0]
