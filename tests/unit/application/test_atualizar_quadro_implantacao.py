"""Testes do caso de uso AtualizarQuadroImplantacao."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.use_cases.atualizar_quadro_implantacao import (
    AtualizarQuadroImplantacao,
    ComandoAtualizarQuadroImplantacao,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)


def _empresa() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="6201500",
        uf="SP",
        setor_macro=SetorMacro.SERVICOS,
    )


def _diag_finalizado() -> Diagnostico:
    return Diagnostico(
        tenant_id=uuid4(),
        empresa=_empresa(),
        respondente=Respondente(email="a@b.com", nome="N"),
        plano=PlanoDiagnostico.GRATUITO,
        status=StatusDiagnostico.FINALIZADO,
        score_geral=50.0,
    )


@pytest.mark.asyncio
class TestAtualizarQuadroImplantacao:
    """Persistência com lock otimista (port mock)."""

    async def test_nao_encontrado(self) -> None:
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=None)
        uc = AtualizarQuadroImplantacao(repo=repo)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            quadro_implantacao_anotacoes={"f0_a0": {"comentario": "x", "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(DiagnosticoNaoEncontradoError):
            await uc.execute(cmd)

    async def test_conflito_versao(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=None)
        uc = AtualizarQuadroImplantacao(repo=repo)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes={"f0_a0": {"comentario": "x", "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(ConflitoVersaoOtimistaError):
            await uc.execute(cmd)

    async def test_sucesso(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo)
        blob = {"f0_a0": {"comentario": "Kickoff", "prazo_meta": "2026-12-31"}}
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes=blob,
            versao_esperada=1,
        )
        out = await uc.execute(cmd)
        assert out is d
        repo.atualizar_quadro_implantacao_com_versao.assert_awaited_once()

    async def test_rejeita_em_andamento(self) -> None:
        d = Diagnostico(
            tenant_id=uuid4(),
            empresa=_empresa(),
            respondente=Respondente(email="a@b.com", nome="N"),
            plano=PlanoDiagnostico.GRATUITO,
            status=StatusDiagnostico.EM_ANDAMENTO,
        )
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes={"f0_a0": {"comentario": "x", "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(ValueError, match="finalizado"):
            await uc.execute(cmd)
