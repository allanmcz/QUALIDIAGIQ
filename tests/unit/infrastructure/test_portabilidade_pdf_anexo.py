"""Testes do PDF de portabilidade com JSON embebido (pikepdf + ReportLab)."""

from __future__ import annotations

import io
import uuid

from pikepdf import Pdf

from src.infrastructure.pdf.portabilidade_pdf_anexo import (
    gerar_pdf_portabilidade_com_json_embebido,
)


def test_gerar_pdf_embebido_produz_pdf_valido_com_anexo() -> None:
    blob = b'{"schema_id":"qdi-diagnostico-export-v1"}'
    did = str(uuid.uuid4())
    tid = str(uuid.uuid4())
    raw = gerar_pdf_portabilidade_com_json_embebido(
        json_bytes=blob,
        diagnostico_id=did,
        tenant_id=tid,
    )
    assert raw.startswith(b"%PDF")
    doc = Pdf.open(io.BytesIO(raw))
    try:
        assert "qdi-diagnostico-export-v1.json" in doc.attachments
    finally:
        doc.close()
