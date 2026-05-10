"""
Geração de PDF com anexo embutido do JSON de export (ADR-012 §4).

Usa **ReportLab** (PDF em Python puro) + **pikepdf** para embutir o JSON (Associated Files).
"""

from __future__ import annotations

import io

from pikepdf import Pdf
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def gerar_pdf_portabilidade_com_json_embebido(
    *,
    json_bytes: bytes,
    diagnostico_id: str,
    tenant_id: str,
) -> bytes:
    """
    Produz PDF com página-resumo em PT-BR e embute ``qdi-diagnostico-export-v1.json`` como anexo.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, height = A4
    y = height - 72
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y, "QualiDiagIQ - Pacote de portabilidade (LGPD art. 18, V)")
    y -= 28
    c.setFont("Helvetica", 11)
    for line in (
        "Documento de resumo humano. O pacote de dados estruturados encontra-se no anexo JSON.",
        f"Diagnostico: {diagnostico_id}",
        f"Tenant: {tenant_id}",
        "Anexo: qdi-diagnostico-export-v1.json",
        "Base: Lei 13.709/2018; ADR-012 QualiDiagIQ.",
    ):
        c.drawString(72, y, line[:200])
        y -= 18
    c.save()
    buf.seek(0)
    pdf = Pdf.open(buf)
    pdf.attachments["qdi-diagnostico-export-v1.json"] = json_bytes
    out = io.BytesIO()
    pdf.save(out)
    out.seek(0)
    return out.read()
