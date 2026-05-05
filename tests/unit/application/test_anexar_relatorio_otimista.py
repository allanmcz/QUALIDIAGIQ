"""Testes do caso de uso AnexarRelatorioOtimista."""

from __future__ import annotations

import copy
import uuid
from unittest.mock import AsyncMock

import pytest

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.ports.diagnostico_mutacao_audit_port import TipoMutacaoDiagnostico
from src.application.use_cases.anexar_relatorio_otimista import (
    AnexarRelatorioOtimista,
    ComandoAnexarRelatorioOtimista,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.infrastructure.adapters.noop_diagnostico_mutacao_audit_adapter import (
    NoOpDiagnosticoMutacaoAuditAdapter,
)


def _diag_finalizado() -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="UC LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=uuid.uuid4(),
        empresa=empresa,
        respondente=Respondente(email="uc@teste.com"),
    )
    d.finalizar(60.0)
    return d


_NOOP_AUDIT = NoOpDiagnosticoMutacaoAuditAdapter()


@pytest.mark.asyncio
async def test_nao_encontrado() -> None:
    repo = AsyncMock()
    repo.buscar_por_id.return_value = None
    uc = AnexarRelatorioOtimista(repo=repo, mutacao_audit=_NOOP_AUDIT)
    cmd = ComandoAnexarRelatorioOtimista(
        tenant_id=uuid.uuid4(),
        diagnostico_id=uuid.uuid4(),
        relatorio_pdf_url="https://exemplo/p.pdf",
        versao_esperada=1,
    )
    with pytest.raises(DiagnosticoNaoEncontradoError):
        await uc.execute(cmd)


@pytest.mark.asyncio
async def test_rejeita_nao_finalizado() -> None:
    repo = AsyncMock()
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="UC LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=uuid.uuid4(),
        empresa=empresa,
        respondente=Respondente(email="uc@teste.com"),
    )
    repo.buscar_por_id.return_value = d
    uc = AnexarRelatorioOtimista(repo=repo, mutacao_audit=_NOOP_AUDIT)
    cmd = ComandoAnexarRelatorioOtimista(
        tenant_id=d.tenant_id,
        diagnostico_id=d.id,
        relatorio_pdf_url="https://exemplo/p.pdf",
        versao_esperada=1,
    )
    with pytest.raises(ValueError, match="finalizado"):
        await uc.execute(cmd)


@pytest.mark.asyncio
async def test_conflito_versao_otimista() -> None:
    d = _diag_finalizado()
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d
    repo.atualizar_relatorio_pdf_com_versao.return_value = None
    uc = AnexarRelatorioOtimista(repo=repo, mutacao_audit=_NOOP_AUDIT)
    cmd = ComandoAnexarRelatorioOtimista(
        tenant_id=d.tenant_id,
        diagnostico_id=d.id,
        relatorio_pdf_url="https://exemplo/p.pdf",
        versao_esperada=1,
    )
    with pytest.raises(ConflitoVersaoOtimistaError):
        await uc.execute(cmd)


@pytest.mark.asyncio
async def test_sucesso_retorna_entidade_atualizada() -> None:
    d = _diag_finalizado()
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d
    d_ok = copy.deepcopy(d)
    d_ok.anexar_relatorio("https://exemplo/p.pdf")
    d_ok.versao_otimista = 2
    repo.atualizar_relatorio_pdf_com_versao.return_value = d_ok
    audit = AsyncMock()
    actor = uuid.uuid4()
    uc = AnexarRelatorioOtimista(repo=repo, mutacao_audit=audit)
    cmd = ComandoAnexarRelatorioOtimista(
        tenant_id=d.tenant_id,
        diagnostico_id=d.id,
        relatorio_pdf_url="https://exemplo/p.pdf",
        versao_esperada=1,
        actor_user_id=actor,
    )
    out = await uc.execute(cmd)
    assert out.relatorio_pdf_url == "https://exemplo/p.pdf"
    assert out.versao_otimista == 2
    audit.registrar.assert_awaited_once()
    kw = audit.registrar.await_args.kwargs
    assert kw["tipo"] == TipoMutacaoDiagnostico.RELATORIO_PDF
    assert kw["actor_user_id"] == actor
    assert kw["versao_otimista_antes"] == 1
    assert kw["versao_otimista_apos"] == 2


@pytest.mark.asyncio
async def test_auditoria_falha_nao_impede_sucesso() -> None:
    d = _diag_finalizado()
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d
    d_ok = copy.deepcopy(d)
    d_ok.anexar_relatorio("https://exemplo/p.pdf")
    d_ok.versao_otimista = 2
    repo.atualizar_relatorio_pdf_com_versao.return_value = d_ok
    audit = AsyncMock()
    audit.registrar.side_effect = OSError("disk")
    uc = AnexarRelatorioOtimista(repo=repo, mutacao_audit=audit)
    cmd = ComandoAnexarRelatorioOtimista(
        tenant_id=d.tenant_id,
        diagnostico_id=d.id,
        relatorio_pdf_url="https://exemplo/p.pdf",
        versao_esperada=1,
    )
    out = await uc.execute(cmd)
    assert out.versao_otimista == 2
    audit.registrar.assert_awaited_once()
