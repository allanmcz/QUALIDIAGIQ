"""Testes do caso de uso BuscarCnaeSubclasses (APPLICATION)."""

from __future__ import annotations

import pytest

from src.application.ports.cnae_subclasse_consulta_port import CnaeSubclasseConsultaPort
from src.application.use_cases.buscar_cnae_subclasses import BuscarCnaeSubclasses
from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo


class _RepoFake(CnaeSubclasseConsultaPort):
    async def buscar(self, *, consulta: str, limite: int) -> list[CnaeSubclasseResumo]:
        assert consulta == "62"
        assert limite == 10
        return [CnaeSubclasseResumo(subclasse_id="6201501", descricao="Software sob encomenda")]


class TestBuscarCnaeSubclasses:
    @pytest.mark.asyncio
    async def test_executa_e_respeita_limite_encapsulado(self) -> None:
        uc = BuscarCnaeSubclasses(repo=_RepoFake())
        out = await uc.execute("  62  ", 10)
        assert len(out) == 1
        assert out[0].subclasse_id == "6201501"

    @pytest.mark.asyncio
    async def test_rejeita_consulta_curta(self) -> None:
        uc = BuscarCnaeSubclasses(repo=_RepoFake())
        with pytest.raises(ValueError, match="2 caracteres"):
            await uc.execute("1", 20)
