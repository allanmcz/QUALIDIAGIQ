"""Testes do adapter Supabase Storage (upload PDF e fallback mock em não-produção)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

import src.infrastructure.adapters.storage_supabase as storage_mod
from src.infrastructure.adapters.storage_supabase import SupabaseStorageAdapter


@pytest.fixture
def mock_bucket() -> MagicMock:
    b = MagicMock()
    b.upload.return_value = None
    b.get_public_url.return_value = "https://example.supabase.co/storage/v1/object/public/x.pdf"
    return b


@pytest.fixture
def mock_client(mock_bucket: MagicMock) -> MagicMock:
    c = MagicMock()
    c.storage.from_.return_value = mock_bucket
    return c


@pytest.mark.asyncio
async def test_upload_pdf_sucesso_retorna_url_publica(
    mock_client: MagicMock, mock_bucket: MagicMock
) -> None:
    adapter = SupabaseStorageAdapter(mock_client)
    tid, did = uuid4(), uuid4()
    url = await adapter.upload_pdf(tid, did, b"%PDF-1.4")
    assert url.startswith("http")
    mock_bucket.upload.assert_called_once()
    mock_client.storage.from_.assert_called_with("relatorios_qdi")


@pytest.mark.asyncio
async def test_upload_pdf_producao_falha_runtime_error(
    mock_client: MagicMock, mock_bucket: MagicMock
) -> None:
    mock_bucket.upload.side_effect = OSError("storage indisponível")
    settings = MagicMock()
    settings.app_env = "production"

    with patch.object(storage_mod, "get_settings", return_value=settings):
        adapter = SupabaseStorageAdapter(mock_client)
        with pytest.raises(RuntimeError, match="produção"):
            await adapter.upload_pdf(uuid4(), uuid4(), b"x")


@pytest.mark.asyncio
async def test_upload_pdf_desenvolvimento_fallback_mock_url(
    mock_client: MagicMock,
    mock_bucket: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: object,
) -> None:
    mock_bucket.upload.side_effect = RuntimeError("rede")
    settings = MagicMock()
    settings.app_env = "development"
    settings.qdi_public_api_base_url = "http://127.0.0.1:60000"
    monkeypatch.setenv("QDI_PDF_MOCK_SPOOL_DIR", str(tmp_path))
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    try:
        with (
            patch.object(storage_mod, "get_settings", return_value=settings),
            patch.object(storage_mod, "pdf_mock_existe_em_disco", return_value=True),
        ):
            adapter = SupabaseStorageAdapter(mock_client)
            url = await adapter.upload_pdf(uuid4(), uuid4(), b"%PDF")
        assert "/mock-storage/" in url
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_upload_pdf_fallback_sem_persistencia_disco_regista_erro(
    mock_client: MagicMock,
    mock_bucket: MagicMock,
) -> None:
    mock_bucket.upload.side_effect = RuntimeError("upload")
    settings = MagicMock()
    settings.app_env = "staging"
    settings.qdi_public_api_base_url = "http://api.test"

    with (
        patch.object(storage_mod, "get_settings", return_value=settings),
        patch.object(storage_mod, "pdf_mock_existe_em_disco", return_value=False),
        patch.object(storage_mod, "logger") as log_mock,
    ):
        adapter = SupabaseStorageAdapter(mock_client)
        url = await adapter.upload_pdf(uuid4(), uuid4(), b"%PDF")

    assert "/mock-storage/" in url
    log_mock.error.assert_called()
    nom_evento = log_mock.error.call_args[0][0]
    assert nom_evento == "supabase_storage_fallback_mock_sem_persistencia_disco"
