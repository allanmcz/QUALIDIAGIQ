"""
Desarquivar empresa no painel ao reativar relacionamento (novo ciclo).

Camada: Application
"""

from __future__ import annotations

from uuid import UUID  # noqa: TC003

import structlog

from src.application.ports.empresa_painel_arquivo_port import EmpresaPainelArquivoPort

logger = structlog.get_logger(__name__)


async def desarquivar_empresa_painel_se_necessario(
    arquivo_port: EmpresaPainelArquivoPort,
    *,
    tenant_id: UUID,
    empresa_cnpj: str,
    actor_user_id: UUID | None = None,
) -> bool:
    """
    Remove flag de arquivo se o CNPJ estiver arquivado.

    Returns:
        True se a empresa foi desarquivada nesta chamada.
    """
    cnpj = "".join(ch for ch in empresa_cnpj if ch.isdigit())
    if len(cnpj) != 14:
        return False
    if not await arquivo_port.esta_arquivada(tenant_id, cnpj):
        return False
    mudou = await arquivo_port.definir_arquivado(
        tenant_id,
        cnpj,
        arquivado=False,
        actor_user_id=actor_user_id,
    )
    if mudou:
        logger.info(
            "empresa_painel_desarquivada",
            tenant_id=str(tenant_id),
            empresa_cnpj=cnpj,
        )
    return mudou
