from uuid import UUID

from supabase import Client

from src.application.ports.storage_service import StorageServicePort


class SupabaseStorageService(StorageServicePort):
    """
    Adapter para o Supabase Storage.
    """

    def __init__(self, client: Client, bucket_name: str = "diagnosticos-pdfs"):
        self.client = client
        self.bucket_name = bucket_name

    async def upload_pdf(self, tenant_id: UUID, diagnostico_id: UUID, file_bytes: bytes) -> str:
        """
        Sobe o PDF gerado para o Supabase Storage e retorna a URL pública.
        """
        # Caminho do arquivo: tenant_id/diagnostico_id.pdf para isolamento
        file_path = f"{tenant_id}/{diagnostico_id}.pdf"

        # Realiza o upload (upsert para sobrescrever se já existir)
        # Como o método do Supabase sync-python client é síncrono, faríamos run_in_executor
        # para produção. Mas para o MVP vamos usar direto.
        self.client.storage.from_(self.bucket_name).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )

        # Obtém a URL pública do arquivo
        public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        return public_url
