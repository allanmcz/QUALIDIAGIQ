from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

from src.application.ports.storage_service import StorageServicePort
from src.infrastructure.config.settings import get_settings
from src.infrastructure.storage.mock_pdf_bytes_cache import registrar_pdf_mock

if TYPE_CHECKING:
    from uuid import UUID

    from supabase import Client

logger = structlog.get_logger(__name__)


class SupabaseStorageAdapter(StorageServicePort):
    """
    Adapter para salvar relatórios PDF no Supabase Storage.
    """

    def __init__(self, client: Client, bucket_name: str = "relatorios_qdi") -> None:
        self.client = client
        self.bucket_name = bucket_name

    async def upload_pdf(self, tenant_id: UUID, diagnostico_id: UUID, file_bytes: bytes) -> str:
        """
        Faz o upload do binário para o bucket e retorna a public URL (ou signed URL se preferível).
        Caminho no bucket: tenant_id/diagnostico_id.pdf
        """
        file_path = f"{tenant_id}/{diagnostico_id}.pdf"

        def _upload() -> str:
            try:
                self.client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=file_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"},
                )
                public = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
                return str(public)
            except Exception as e:
                settings = get_settings()
                if (settings.app_env or "").strip().lower() == "production":
                    logger.error(
                        "supabase_storage_upload_falhou_producao",
                        path=file_path,
                        erro=str(e),
                        exc_info=True,
                    )
                    raise RuntimeError(
                        "Upload do PDF para o Supabase Storage falhou em produção. "
                        "Verifique bucket, políticas e SUPABASE_*."
                    ) from e
                registrar_pdf_mock(file_path, file_bytes)
                base = settings.qdi_public_api_base_url.strip().rstrip("/")
                url_fallback = f"{base}/mock-storage/{file_path}"
                logger.warning(
                    "supabase_storage_fallback_mock",
                    path=file_path,
                    url=url_fallback,
                    erro=str(e),
                )
                return url_fallback

        return await asyncio.to_thread(_upload)
