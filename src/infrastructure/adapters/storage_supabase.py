from uuid import UUID

from supabase import Client

from src.application.ports.storage_service import StorageServicePort


class SupabaseStorageAdapter(StorageServicePort):
    """
    Adapter para salvar relatórios PDF no Supabase Storage.
    """

    def __init__(self, client: Client, bucket_name: str = "relatorios_qdi"):
        self.client = client
        self.bucket_name = bucket_name

    async def upload_pdf(self, tenant_id: UUID, diagnostico_id: UUID, file_bytes: bytes) -> str:
        """
        Faz o upload do binário para o bucket e retorna a public URL (ou signed URL se preferível).
        Caminho no bucket: tenant_id/diagnostico_id.pdf
        """
        file_path = f"{tenant_id}/{diagnostico_id}.pdf"

        # Tentar realizar upload (sobrescreve se já existir para simplificar MVP)
        import asyncio
        
        def _upload() -> str:
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            # Para MVP, assume bucket público e recupera a URL pública.
            # Se fosse privado, criaríamos signed url.
            return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        
        url = await asyncio.to_thread(_upload)
        return url # type: ignore
