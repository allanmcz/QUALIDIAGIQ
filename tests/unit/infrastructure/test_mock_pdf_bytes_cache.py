"""Testes do cache em memória + spool em disco do fallback `/mock-storage` (camada INFRA)."""

from pathlib import Path
from uuid import uuid4

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
        tid = uuid4()
        did = uuid4()
        chave = f"{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"%PDF-1.4 teste")
        assert obter_pdf_mock(chave) == b"%PDF-1.4 teste"

    def test_chave_com_barra_inicial_normaliza(self) -> None:
        tid = uuid4()
        did = uuid4()
        chave = f"/{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"x")
        assert obter_pdf_mock(f"{tid}/{did}.pdf") == b"x"

    def test_obter_recupera_do_disco_apos_limpar_memoria(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid = uuid4()
        did = uuid4()
        chave = f"{tid}/{did}.pdf"
        payload = b"%PDF-1.4 disco"
        registrar_pdf_mock(chave, payload)
        assert pdf_mock_existe_em_disco(chave) is True
        limpar_apenas_memoria_para_teste()
        assert obter_pdf_mock(chave) == payload
        get_settings.cache_clear()

    def test_chave_invalida_nao_escrita_em_disco_mas_fica_em_ram(self) -> None:
        tid = uuid4()
        did = uuid4()
        chave_ruim = f"x_{tid}/{did}.pdf"
        registrar_pdf_mock(chave_ruim, b"apenas_ram")
        assert pdf_mock_existe_em_disco(chave_ruim) is False
        assert obter_pdf_mock(chave_ruim) == b"apenas_ram"

    def test_obter_read_bytes_oserror_devolve_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid = uuid4()
        did = uuid4()
        chave = f"{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"antes")
        limpar_apenas_memoria_para_teste()
        orig_read = Path.read_bytes

        def _read_boom(self: Path) -> bytes:
            raise OSError("leitura falhou")

        monkeypatch.setattr(Path, "read_bytes", _read_boom)
        try:
            assert obter_pdf_mock(chave) is None
        finally:
            monkeypatch.setattr(Path, "read_bytes", orig_read)
            get_settings.cache_clear()

    def test_lru_evicta_primeiro_item_da_ram_mas_rele_do_disco(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        chaves: list[str] = []
        for _ in range(65):
            t, d = uuid4(), uuid4()
            chaves.append(f"{t}/{d}.pdf")
            registrar_pdf_mock(chaves[-1], f"pdf-{chaves[-1]}".encode())

        primeiro = chaves[0]
        assert pdf_mock_existe_em_disco(primeiro) is True
        limpar_apenas_memoria_para_teste()
        assert obter_pdf_mock(primeiro).decode() == f"pdf-{primeiro}"
        get_settings.cache_clear()
