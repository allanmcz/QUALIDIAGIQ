"""Testes do caso de uso AtualizarChecklistM12Autoconf — camada APPLICATION."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.ports.diagnostico_mutacao_audit_port import TipoMutacaoDiagnostico
from src.application.use_cases.atualizar_checklist_m12_autoconf import (
    AtualizarChecklistM12Autoconf,
    ComandoAtualizarChecklistM12Autoconf,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    DiagnosticoNaoFinalizavelError,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)


def _diag_finalizado(tid: uuid.UUID) -> Diagnostico:
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="M12 LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(tenant_id=tid, empresa=empresa, respondente=Respondente(email="m12@teste.com"))
    d.finalizar(55.0)
    return d


@pytest.mark.asyncio
async def test_execute_persiste_e_retorna_atualizado():
    tid = uuid.uuid4()
    did = uuid.uuid4()
    d0 = _diag_finalizado(tid)
    d0.id = did

    d1 = _diag_finalizado(tid)
    d1.id = did
    d1.definir_checklist_m12_autoconf([5] * 10)
    d1.versao_otimista = 2

    repo = AsyncMock()
    repo.buscar_por_id.return_value = d0
    repo.atualizar_checklist_m12_com_versao.return_value = d1

    audit = AsyncMock()
    uc = AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=audit)
    actor = uuid.uuid4()
    cmd = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tid,
        diagnostico_id=did,
        checklist_m12_autoconf=[5] * 10,
        versao_esperada=1,
        actor_user_id=actor,
    )
    out = await uc.execute(cmd)

    assert out.versao_otimista == 2
    assert out.checklist_m12_estado == [5] * 10
    repo.atualizar_checklist_m12_com_versao.assert_awaited_once_with(did, tid, [5] * 10, 1)
    audit.registrar.assert_awaited_once()
    call_kw = audit.registrar.await_args.kwargs
    assert call_kw["tipo"] == TipoMutacaoDiagnostico.M12_LIKERT
    assert call_kw["actor_user_id"] == actor
    assert call_kw["versao_otimista_antes"] == 1
    assert call_kw["versao_otimista_apos"] == 2


@pytest.mark.asyncio
async def test_execute_nao_encontrado():
    repo = AsyncMock()
    repo.buscar_por_id.return_value = None
    audit = AsyncMock()
    uc = AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=audit)
    cmd = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=uuid.uuid4(),
        diagnostico_id=uuid.uuid4(),
        checklist_m12_autoconf=[1] * 10,
        versao_esperada=1,
    )
    with pytest.raises(DiagnosticoNaoEncontradoError):
        await uc.execute(cmd)
    audit.registrar.assert_not_called()


@pytest.mark.asyncio
async def test_execute_conflito_versao():
    tid = uuid.uuid4()
    d0 = _diag_finalizado(tid)
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d0
    repo.atualizar_checklist_m12_com_versao.return_value = None
    audit = AsyncMock()
    uc = AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=audit)
    cmd = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tid,
        diagnostico_id=d0.id,
        checklist_m12_autoconf=[1] * 10,
        versao_esperada=99,
    )
    with pytest.raises(ConflitoVersaoOtimistaError):
        await uc.execute(cmd)
    audit.registrar.assert_not_called()


@pytest.mark.asyncio
async def test_execute_rejeita_em_andamento():
    tid = uuid.uuid4()
    empresa = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=tid,
        empresa=empresa,
        respondente=Respondente(email="x@teste.com"),
    )
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d
    audit = AsyncMock()
    uc = AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=audit)
    cmd = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tid,
        diagnostico_id=d.id,
        checklist_m12_autoconf=[1] * 10,
        versao_esperada=1,
    )
    with pytest.raises(DiagnosticoNaoFinalizavelError, match=r"finalizado"):
        await uc.execute(cmd)
    audit.registrar.assert_not_called()


@pytest.mark.asyncio
async def test_execute_auditoria_falha_nao_impede_sucesso() -> None:
    tid = uuid.uuid4()
    did = uuid.uuid4()
    d0 = _diag_finalizado(tid)
    d0.id = did
    d1 = _diag_finalizado(tid)
    d1.id = did
    d1.definir_checklist_m12_autoconf([3] * 10)
    d1.versao_otimista = 2
    repo = AsyncMock()
    repo.buscar_por_id.return_value = d0
    repo.atualizar_checklist_m12_com_versao.return_value = d1
    audit = AsyncMock()
    audit.registrar.side_effect = RuntimeError("indisponível")
    uc = AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=audit)
    cmd = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tid,
        diagnostico_id=did,
        checklist_m12_autoconf=[3] * 10,
        versao_esperada=1,
    )
    out = await uc.execute(cmd)
    assert out.versao_otimista == 2
    audit.registrar.assert_awaited_once()
