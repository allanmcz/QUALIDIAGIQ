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
            try:
                self.client.storage.from_(self.bucket_name).upload(
                    path=file_path,
                    file=file_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"}
                )
                return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            except Exception as e:
                print(f"Aviso: Falha ao fazer upload para o Supabase Storage ({e}). Retornando URL mockada.")
                return f"http://localhost:8000/mock-storage/{file_path}"
        
        url = await asyncio.to_thread(_upload)
        return url # type: ignore
