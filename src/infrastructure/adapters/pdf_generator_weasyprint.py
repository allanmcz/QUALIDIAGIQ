from datetime import UTC, datetime
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader
from structlog.contextvars import get_contextvars

from src.application.ports.pdf_generator import PdfGeneratorPort
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.config.settings import get_settings
from src.infrastructure.observability.qdi_otel_metrics import record_pdf_generation
from src.infrastructure.pdf.relatorio_pdf_i18n import (
    formatar_data_geracao_pdf,
    formatar_telefone_exibicao_br,
    nivel_score_labels,
    obter_textos_pdf,
)

logger = structlog.get_logger(__name__)


class WeasyPrintPdfGenerator(PdfGeneratorPort):
    """
    Único motor de PDF do QDI: **WeasyPrint** + Jinja2 (HTML/CSS → PDF).

    Captação de lead na capa do relatório: apenas **e-mail** e **telefone** (minimização na peça PDF).
    Idiomas: ``diagnostico.locale_relatorio`` (**pt-BR** | **en**).
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
        self,
        diagnostico: Diagnostico,
        score: ScoreCompleto,
        recomendacao_ia: str | None = None,
        explicacao_score_llm_texto: str | None = None,
    ) -> bytes:
        """
        Renderiza o template jinja com os dados do diagnóstico e coverte para PDF.
        """
        template = self.jinja_env.get_template("relatorio_diagnostico.html")

        locale_pdf = getattr(diagnostico, "locale_relatorio", "pt-BR") or "pt-BR"
        t = obter_textos_pdf(locale_pdf)
        nivel_mapping = nivel_score_labels(locale_pdf)
        telefone_pdf = formatar_telefone_exibicao_br(diagnostico.respondente.telefone)
        agora = datetime.now(UTC)
        data_geracao = formatar_data_geracao_pdf(locale_pdf, agora)
        html_lang = "en" if locale_pdf == "en" else "pt-BR"

        from src.application.services.consultoria_service import ConsultoriaService

        checklist = ConsultoriaService.gerar_checklist(diagnostico, score)
        matriz_impacto = ConsultoriaService.gerar_matriz_impacto(diagnostico)
        cronograma = ConsultoriaService.gerar_cronograma_cinco_fases()
        piores_dimensoes = sorted(
            score.score_por_dimensao.items(),
            key=lambda kv: kv[1].valor,
        )[:3]
        piores_template = [{"codigo": dim.value, "valor": sn.valor} for dim, sn in piores_dimensoes]

        html_out = template.render(
            diagnostico=diagnostico,
            t=t,
            html_lang=html_lang,
            telefone_lead_exibicao=telefone_pdf,
            score_geral=score.score_geral,
            nivel_geral=nivel_mapping.get(score.score_geral.nivel.name, "N/A"),
            dimensoes=score.score_por_dimensao,
            data_geracao=data_geracao,
            recomendacao_ia=recomendacao_ia,
            explicacao_score_llm_texto=explicacao_score_llm_texto,
            checklist=checklist,
            matriz_impacto=matriz_impacto,
            cronograma=cronograma,
            piores_dimensoes=piores_template,
        )

        pdf_bytes = await self._render_html_bytes(html_out, diagnostico)
        record_pdf_generation(outcome="success")
        return pdf_bytes

    async def gerar_pdf_questionario_respostas(
        self,
        diagnostico: Diagnostico,
        respostas: list[dict[str, object]],
    ) -> bytes:
        """Espelho do questionário — template dedicado (distinto do relatório executivo M04)."""
        template = self.jinja_env.get_template("questionario_respostas.html")
        agora = datetime.now(UTC)
        data_geracao = formatar_data_geracao_pdf(
            getattr(diagnostico, "locale_relatorio", "pt-BR") or "pt-BR",
            agora,
        )
        fin = diagnostico.finalizado_em
        html_out = template.render(
            empresa_razao=diagnostico.empresa.razao_social,
            empresa_cnpj=diagnostico.empresa.cnpj or "",
            diagnostico_id=str(diagnostico.id),
            finalizado_em=(
                fin.astimezone(UTC).strftime("%d/%m/%Y %H:%M UTC") if fin is not None else "—"
            ),
            data_geracao=data_geracao,
            hash_evidencia=diagnostico.hash_evidencia or "",
            respostas=respostas,
        )
        pdf_bytes = await self._render_html_bytes(html_out, diagnostico)
        record_pdf_generation(outcome="success")
        return pdf_bytes

    async def gerar_pdf_comparacao_questionario(
        self,
        comparacao: dict[str, object],
        *,
        contexto_diagnostico: Diagnostico,
    ) -> bytes:
        """Exportação PDF da matriz comparar-questionario."""
        template = self.jinja_env.get_template("comparacao_questionario.html")
        agora = datetime.now(UTC)
        locale = getattr(contexto_diagnostico, "locale_relatorio", "pt-BR") or "pt-BR"
        data_geracao = formatar_data_geracao_pdf(locale, agora)
        ctx = _contexto_template_comparacao(comparacao, data_geracao=data_geracao)
        html_out = template.render(**ctx)
        pdf_bytes = await self._render_html_bytes(html_out, contexto_diagnostico)
        record_pdf_generation(outcome="success")
        return pdf_bytes

    async def _render_html_bytes(self, html_out: str, diagnostico: Diagnostico) -> bytes:
        css_path = str(self.templates_dir / "style.css")
        _ctx = get_contextvars()
        http_tid = _ctx.get("http_trace_id") if isinstance(_ctx, dict) else None

        import asyncio

        def _render() -> bytes:
            try:
                from weasyprint import CSS, HTML

                base_url = self.templates_dir.resolve().as_uri() + "/"
                return bytes(
                    HTML(string=html_out, base_url=base_url).write_pdf(
                        stylesheets=[CSS(filename=css_path)]
                    )
                )
            except Exception as e:
                logger.warning(
                    "weasyprint_indisponivel_pdf_mock",
                    erro=str(e),
                    http_trace_id=http_tid,
                    diagnostico_id=str(diagnostico.id),
                    tenant_id=str(diagnostico.tenant_id),
                    exc_info=True,
                )
                record_pdf_generation(outcome="mock_fallback")
                return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] /Count 0 >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

        timeout_s = float(get_settings().pdf_render_timeout_seconds)
        try:
            return bytes(
                await asyncio.wait_for(asyncio.to_thread(_render), timeout=timeout_s)
            )
        except TimeoutError:
            record_pdf_generation(outcome="timeout")
            raise RuntimeError(
                f"Timeout ao gerar PDF (>{timeout_s}s). Ajuste QDI_PDF_RENDER_TIMEOUT_SECONDS."
            ) from None


def _contexto_template_comparacao(
    comparacao: dict[str, object],
    *,
    data_geracao: str,
) -> dict[str, object]:
    """Normaliza payload da API para o template Jinja de comparação."""
    meta_raw = comparacao.get("diagnosticos")
    linhas_raw = comparacao.get("linhas")
    if not isinstance(meta_raw, list) or not isinstance(linhas_raw, list):
        raise ValueError("Payload de comparação inválido para PDF")

    colunas: list[dict[str, str]] = []
    for m in meta_raw:
        if not isinstance(m, dict):
            continue
        did = str(m.get("diagnostico_id", ""))
        fin = m.get("finalizado_em")
        data_txt = "—"
        if isinstance(fin, str) and fin:
            try:
                dt = datetime.fromisoformat(fin.replace("Z", "+00:00"))
                data_txt = dt.astimezone(UTC).strftime("%d/%m/%y")
            except ValueError:
                data_txt = fin[:10]
        n_int = m.get("numero_interno_grupo")
        n = f"#{n_int}" if n_int is not None else did[:8]
        score = m.get("score_geral")
        score_txt = f"{float(score):.1f}" if score is not None else "—"
        colunas.append({"id": did, "rotulo": f"{n} · {data_txt} · {score_txt}"})

    diag_ids = [c["id"] for c in colunas]
    linhas_pdf: list[dict[str, object]] = []
    for linha in linhas_raw:
        if not isinstance(linha, dict):
            continue
        valores_in = linha.get("valores_por_diagnostico")
        valores_out: dict[str, dict[str, object]] = {}
        exibicoes: list[str] = []
        if isinstance(valores_in, dict):
            for did in diag_ids:
                v = valores_in.get(did)
                if isinstance(v, dict):
                    txt = str(v.get("valor_exibicao", "—"))
                    valores_out[did] = {
                        "valor_exibicao": txt,
                        "excluida_calculo": bool(v.get("excluida_calculo")),
                    }
                    exibicoes.append(txt)
                else:
                    valores_out[did] = {"valor_exibicao": "—", "excluida_calculo": False}
                    exibicoes.append("—")
        destaque = len(exibicoes) > 1 and len(set(exibicoes)) > 1
        linhas_pdf.append(
            {
                "pergunta_codigo": str(linha.get("pergunta_codigo", "")),
                "texto_pergunta": str(linha.get("texto_pergunta", "")),
                "base_legal": linha.get("base_legal"),
                "valores": valores_out,
                "destaque_mudanca": destaque,
            }
        )

    return {
        "empresa_razao": str(comparacao.get("empresa_razao_social", "")),
        "empresa_cnpj": str(comparacao.get("empresa_cnpj", "")),
        "data_geracao": data_geracao,
        "diagnosticos": meta_raw,
        "colunas": colunas,
        "linhas": linhas_pdf,
    }
