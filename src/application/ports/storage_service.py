from abc import ABC, abstractmethod
from uuid import UUID


class StorageServicePort(ABC):
    """
    Porta (Interface) para armazenamento de arquivos (ex: Supabase Storage).
    
    Camada: Application
    """
    
    @abstractmethod
    async def upload_pdf(self, tenant_id: UUID, diagnostico_id: UUID, file_bytes: bytes) -> str:
        """
        Faz o upload de um arquivo PDF e retorna a URL pública/assinada.
        
        Args:
            tenant_id: UUID do tenant para isolamento de dados
            diagnostico_id: UUID do diagnóstico, usado no nome do arquivo
            file_bytes: Conteúdo binário do PDF
            
        Returns:
            URL do arquivo salvo
        """
        pass
