"""Testes de desarquivamento automático no painel."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.services.empresa_painel_desarquivar import (
    desarquivar_empresa_painel_se_necessario,
)
from src.infrastructure.adapters.memoria_empresa_painel_arquivo_adapter import (
    MemoriaEmpresaPainelArquivoAdapter,
)


class TestDesarquivarEmpresaPainelSeNecessario:
    @pytest.mark.asyncio
    async def test_desarquiva_quando_estava_arquivada(self) -> None:
        port = MemoriaEmpresaPainelArquivoAdapter()
        tid = uuid4()
        cnpj = "11222333000181"
        await port.definir_arquivado(tid, cnpj, arquivado=True, actor_user_id=None)
        mudou = await desarquivar_empresa_painel_se_necessario(
            port, tenant_id=tid, empresa_cnpj=cnpj
        )
        assert mudou is True
        assert not await port.esta_arquivada(tid, cnpj)

    @pytest.mark.asyncio
    async def test_nao_faz_nada_se_ja_visivel(self) -> None:
        port = MemoriaEmpresaPainelArquivoAdapter()
        tid = uuid4()
        cnpj = "11222333000181"
        mudou = await desarquivar_empresa_painel_se_necessario(
            port, tenant_id=tid, empresa_cnpj=cnpj
        )
        assert mudou is False
