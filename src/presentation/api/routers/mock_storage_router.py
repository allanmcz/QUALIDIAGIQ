"""
Rota HTTP para servir PDF em fallback quando o Storage Supabase não está disponível.

Camada: Presentation
Uso: apenas desenvolvimento / demo — URL gerada por `SupabaseStorageAdapter` após falha de upload.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — FastAPI usa o tipo do parâmetro de path em runtime

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response

from src.infrastructure.storage.mock_pdf_bytes_cache import obter_pdf_mock

router = APIRouter(tags=["Infra — PDF mock (dev)"])


@router.get("/mock-storage/{tenant_id}/{nome_arquivo}")
async def baixar_pdf_mock_storage(tenant_id: uuid.UUID, nome_arquivo: str) -> Response:
    """
    Devolve o PDF colocado em cache quando o upload ao bucket falhou.

    Não substitui Storage real em produção.
    """
    if "/" in nome_arquivo or "\\" in nome_arquivo or ".." in nome_arquivo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo inválido (path traversal).",
        )
    if not nome_arquivo.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Apenas ficheiros .pdf.")

    chave = f"{tenant_id}/{nome_arquivo}"
    dados = obter_pdf_mock(chave)
    if dados is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "PDF não encontrado no spool em disco nem na RAM. Possíveis causas: "
                "caminho QDI_PDF_MOCK_SPOOL_DIR sem volume após recriar o container; "
                "LRU em RAM evictou e o ficheiro em disco foi apagado; ou nunca foi gerado. "
                "Gere de novo o diagnóstico, defina volume em /tmp/qdi-mock-pdf (default do spool) "
                "ou configure upload real no Supabase Storage."
            ),
        )

    return Response(
        content=dados,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{nome_arquivo}"',
            "Cache-Control": "no-store",
        },
    )
