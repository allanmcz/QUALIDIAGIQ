"""Testes do caso de uso ArquivarEmpresaPainel."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.use_cases.arquivar_empresa_painel import (
    ArquivarEmpresaPainel,
    ComandoArquivarEmpresaPainel,
)
from src.infrastructure.adapters.memoria_empresa_painel_arquivo_adapter import (
    MemoriaEmpresaPainelArquivoAdapter,
)


class TestArquivarEmpresaPainel:
    @pytest.mark.asyncio
    async def test_arquiva_e_restaura(self) -> None:
        port = MemoriaEmpresaPainelArquivoAdapter()
        uc = ArquivarEmpresaPainel(arquivo_port=port)
        tid = uuid4()
        cnpj = "11222333000181"
        out1 = await uc.execute(
            ComandoArquivarEmpresaPainel(
                tenant_id=tid,
                actor_user_id=uuid4(),
                empresa_cnpj=cnpj,
                arquivado=True,
            )
        )
        assert out1.arquivado is True
        assert out1.estado_alterado is True
        assert await port.esta_arquivada(tid, cnpj)
        out2 = await uc.execute(
            ComandoArquivarEmpresaPainel(
                tenant_id=tid,
                actor_user_id=uuid4(),
                empresa_cnpj=cnpj,
                arquivado=False,
            )
        )
        assert out2.arquivado is False
        assert not await port.esta_arquivada(tid, cnpj)
