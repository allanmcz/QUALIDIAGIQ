"""Testes do cache em memória usado pelo fallback `/mock-storage` (camada INFRA)."""

import uuid

from src.infrastructure.storage.mock_pdf_bytes_cache import obter_pdf_mock, registrar_pdf_mock


class TestMockPdfBytesCache:
    """Invariantes do LRU em memória para PDF mock."""

    def test_registrar_e_obter(self) -> None:
        tid = uuid.uuid4()
        did = uuid.uuid4()
        chave = f"{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"%PDF-1.4 teste")
        assert obter_pdf_mock(chave) == b"%PDF-1.4 teste"

    def test_chave_com_barra_inicial_normaliza(self) -> None:
        tid = uuid.uuid4()
        did = uuid.uuid4()
        chave = f"/{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"x")
        assert obter_pdf_mock(f"{tid}/{did}.pdf") == b"x"
