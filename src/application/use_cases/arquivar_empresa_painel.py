"""
Arquivar ou restaurar empresa (CNPJ) na listagem do painel — sem apagar diagnósticos.

Camada: Application
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from src.application.ports.empresa_painel_arquivo_port import EmpresaPainelArquivoPort


@dataclass(frozen=True)
class ComandoArquivarEmpresaPainel:
    tenant_id: UUID
    actor_user_id: UUID
    empresa_cnpj: str
    arquivado: bool


@dataclass(frozen=True)
class ResultadoArquivarEmpresaPainel:
    empresa_cnpj: str
    arquivado: bool
    estado_alterado: bool


class ArquivarEmpresaPainel:
    """Oculta ou restaura empresa no painel principal (evidência WORM intacta)."""

    def __init__(self, arquivo_port: EmpresaPainelArquivoPort) -> None:
        self._arquivo = arquivo_port

    async def execute(self, cmd: ComandoArquivarEmpresaPainel) -> ResultadoArquivarEmpresaPainel:
        mudou = await self._arquivo.definir_arquivado(
            cmd.tenant_id,
            cmd.empresa_cnpj,
            arquivado=cmd.arquivado,
            actor_user_id=cmd.actor_user_id,
        )
        return ResultadoArquivarEmpresaPainel(
            empresa_cnpj=cmd.empresa_cnpj,
            arquivado=cmd.arquivado,
            estado_alterado=mudou,
        )
