"""Testes do cache em memória + spool em disco do fallback `/mock-storage` (camada INFRA)."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import src.infrastructure.storage.mock_pdf_bytes_cache as mock_pdf_bytes_cache
from src.infrastructure.config.settings import get_settings
from src.infrastructure.storage.mock_pdf_bytes_cache import (
    _caminho_arquivo_spool,
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

    def test_obter_chave_valida_sem_ram_sem_ficheiro_retorna_none(self) -> None:
        """Sem LRU nem ficheiro no spool ⇒ ``None`` (final da função)."""
        limpar_apenas_memoria_para_teste()
        t, d = uuid4(), uuid4()
        assert obter_pdf_mock(f"{t}/{d}.pdf") is None

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

    def test_registrar_write_bytes_oserror_mantem_apenas_ram(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid, did = uuid4(), uuid4()
        chave = f"{tid}/{did}.pdf"

        def _write_boom(self: Path, _data: bytes) -> None:
            raise OSError("disco indisponível")

        monkeypatch.setattr(Path, "write_bytes", _write_boom)
        with patch.object(mock_pdf_bytes_cache, "logger") as log_erro:
            registrar_pdf_mock(chave, b"somente_memoria")
        assert obter_pdf_mock(chave) == b"somente_memoria"
        log_erro.error.assert_called_once()
        nom_evento = log_erro.error.call_args[0][0]
        assert nom_evento == "pdf_mock_spool_escrita_falhou"
        assert log_erro.error.call_args[1]["chave"] == chave
        get_settings.cache_clear()

    def test_registrar_oserror_em_chmod_suprimido(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid, did = uuid4(), uuid4()
        chave = f"{tid}/{did}.pdf"

        def _chmod_raise(*_a: object, **_k: object) -> None:
            raise PermissionError("chmod negado")

        monkeypatch.setattr(os, "chmod", _chmod_raise)
        registrar_pdf_mock(chave, b"chmod_ignorado")
        assert pdf_mock_existe_em_disco(chave) is True
        get_settings.cache_clear()

    def test_registrar_duas_vezes_atualiza_bytes(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid, did = uuid4(), uuid4()
        chave = f"{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"v1")
        registrar_pdf_mock(chave, b"v2")
        assert obter_pdf_mock(chave) == b"v2"
        get_settings.cache_clear()

    def test_obter_disco_injecta_ram_entre_locks_prioriza_ram(self, tmp_path, monkeypatch) -> None:
        """Segundo ``with _lock``: outro “writer” pode ter repovoado o LRU antes do insert do disco."""
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        tid, did = uuid4(), uuid4()
        chave = f"{tid}/{did}.pdf"
        registrar_pdf_mock(chave, b"blob_disco")
        limpar_apenas_memoria_para_teste()
        orig_read = Path.read_bytes

        def read_e_injecta(self: Path) -> bytes:
            with mock_pdf_bytes_cache._lock:
                mock_pdf_bytes_cache._store[chave] = b"ganhou_ram"
            return orig_read(self)

        monkeypatch.setattr(Path, "read_bytes", read_e_injecta)
        try:
            assert obter_pdf_mock(chave) == b"ganhou_ram"
        finally:
            monkeypatch.setattr(Path, "read_bytes", orig_read)
            get_settings.cache_clear()

    def test_caminho_spool_partes_diferentes_de_dois_retorna_none(self, monkeypatch) -> None:
        """``len(partes) != 2`` — defesa mesmo após ``match`` truthy."""
        real = mock_pdf_bytes_cache._CHAVE_SEGURA

        class _RegexFalso:
            def match(self, s: str) -> MagicMock | None:
                return MagicMock() if s == "a/b/c.pdf" else real.match(s)

        monkeypatch.setattr(mock_pdf_bytes_cache, "_CHAVE_SEGURA", _RegexFalso())
        assert _caminho_arquivo_spool("a/b/c.pdf") is None

    def test_caminho_spool_stem_nao_uuid_retorna_none(self, monkeypatch) -> None:
        tid = str(uuid4())
        chave = f"{tid}/00000000000000.pdf"
        real = mock_pdf_bytes_cache._CHAVE_SEGURA

        class _RegexFalso:
            def match(self, s: str) -> MagicMock | None:
                return MagicMock() if s == chave else real.match(s)

        monkeypatch.setattr(mock_pdf_bytes_cache, "_CHAVE_SEGURA", _RegexFalso())
        assert _caminho_arquivo_spool(chave) is None

    def test_obter_do_disco_evicta_lru_quando_ram_cheia(self, tmp_path, monkeypatch) -> None:
        """RAM cheia (3 itens) + novo PDF só em disco → repovoamento expulsa o LRU mais antigo."""
        monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
        get_settings.cache_clear()
        monkeypatch.setattr(mock_pdf_bytes_cache, "_MAX_ITENS", 3)
        limpar_apenas_memoria_para_teste()
        chaves: list[tuple[UUID, UUID]] = [(uuid4(), uuid4()) for _ in range(4)]
        for i in range(3):
            t, d = chaves[i]
            registrar_pdf_mock(f"{t}/{d}.pdf", f"p{i}".encode())
        t4, d4 = chaves[3]
        spool = mock_pdf_bytes_cache._diretorio_spool()
        pdir = spool / str(t4)
        pdir.mkdir(parents=True, exist_ok=True)
        (pdir / f"{d4}.pdf").write_bytes(b"p3-disco")
        ch4 = f"{t4}/{d4}.pdf"
        assert obter_pdf_mock(ch4) == b"p3-disco"
        ch1 = f"{chaves[0][0]}/{chaves[0][1]}.pdf"
        with mock_pdf_bytes_cache._lock:
            assert len(mock_pdf_bytes_cache._store) == 3
            assert ch1 not in mock_pdf_bytes_cache._store
            assert ch4 in mock_pdf_bytes_cache._store
        get_settings.cache_clear()
