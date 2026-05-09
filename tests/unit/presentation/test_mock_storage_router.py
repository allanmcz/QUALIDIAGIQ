"""Testes — rota dev ``/mock-storage`` (validação de nome e extensão)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.presentation.api.main import app

client = TestClient(app)


def test_mock_storage_rejeita_path_traversal() -> None:
    tid = uuid.uuid4()
    r = client.get(f"/mock-storage/{tid}/nome..segmento-duplo.pdf")
    assert r.status_code == 400


def test_mock_storage_rejeita_sem_extensao_pdf() -> None:
    tid = uuid.uuid4()
    r = client.get(f"/mock-storage/{tid}/relatorio.docx")
    assert r.status_code == 404
    assert ".pdf" in r.json()["detail"].lower()


@patch("src.presentation.api.routers.mock_storage_router.obter_pdf_mock", return_value=None)
def test_mock_storage_pdf_nao_encontrado_no_cache(_mock_obter: object) -> None:
    tid = uuid.uuid4()
    arquivo = f"{uuid.uuid4()}.pdf"
    r = client.get(f"/mock-storage/{tid}/{arquivo}")
    assert r.status_code == 404
    assert "spool" in r.json()["detail"].lower()
