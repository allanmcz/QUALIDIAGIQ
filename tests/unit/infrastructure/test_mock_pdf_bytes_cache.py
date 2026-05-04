"""Testes do cache em memória + spool em disco do fallback `/mock-storage` (camada INFRA)."""

import uuid

from src.infrastructure.config.settings import get_settings
from src.infrastructure.storage.mock_pdf_bytes_cache import (
    limpar_apenas_memoria_para_teste,
    obter_pdf_mock,
    pdf_mock_existe_em_disco,
    registrar_pdf_mock,
)


class TestMockPdfBytesCache:
    """Invariantes do LRU em memória e persistência em disco para PDF mock."""

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

    def test_obter_recupera_do_disco_apos_limpar_memoria(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid = uuid.uuid4()
        did = uuid.uuid4()
        chave = f"{tid}/{did}.pdf"
        payload = b"%PDF-1.4 disco"
        registrar_pdf_mock(chave, payload)
        assert pdf_mock_existe_em_disco(chave) is True
        limpar_apenas_memoria_para_teste()
        assert obter_pdf_mock(chave) == payload
        get_settings.cache_clear()
