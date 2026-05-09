"""Testes — ``ConsultarCnpjUseCase``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.services.cnpj_consulta_service import ConsultaCnpjMaterializada
from src.application.use_cases.consultar_cnpj import ComandoConsultarCnpj, ConsultarCnpjUseCase
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)


@pytest.mark.asyncio
async def test_sem_aplicar_diagnostico() -> None:
    exp = datetime.now(UTC) + timedelta(hours=1)
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14="33014556000196",
        payload_bruto={},
        payload_canonico={"cnpj": "33014556000196"},
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    svc = MagicMock()
    svc.materializar_consulta = AsyncMock(return_value=mat)
    uc = ConsultarCnpjUseCase(
        service=svc,
        cnpj_repo=MagicMock(),
        diagnostico_repo=MagicMock(),
    )
    cmd = ComandoConsultarCnpj(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="x",
        force_refresh=False,
        aplicar_no_diagnostico_id=None,
        trace_id=None,
    )
    out, aplicado = await uc.executar_e_materializar(cmd)
    assert out.consulta_id == mat.consulta_id
    assert aplicado is False


@pytest.mark.asyncio
async def test_diagnostico_nao_encontrado_levanta() -> None:
    exp = datetime.now(UTC)
    cid_d = uuid4()
    tenant = uuid4()
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14="33014556000196",
        payload_bruto={},
        payload_canonico={"cnpj": "33014556000196"},
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    svc = MagicMock()
    svc.materializar_consulta = AsyncMock(return_value=mat)
    diag_repo = MagicMock()
    diag_repo.buscar_por_id = AsyncMock(return_value=None)
    cnpj_repo = MagicMock()
    uc = ConsultarCnpjUseCase(service=svc, cnpj_repo=cnpj_repo, diagnostico_repo=diag_repo)
    cmd = ComandoConsultarCnpj(
        tenant_id=tenant,
        cnpj_14="33014556000196",
        idempotency_key="k",
        aplicar_no_diagnostico_id=cid_d,
    )
    with pytest.raises(ValueError, match="não encontrado"):
        await uc.executar_e_materializar(cmd)
    diag_repo.buscar_por_id.assert_awaited_once()
    assert cnpj_repo.atualizar_empresa_diagnostico_em_andamento.call_count == 0


@pytest.mark.asyncio
async def test_aplica_merge_chama_repo_quando_hist_nao_vazio() -> None:
    exp = datetime.now(UTC)
    tid = uuid4()
    cid_d = uuid4()
    empresa = EmpresaInfo(
        cnpj="33014556000196",
        razao_social="Antiga Razão",
        porte=PorteEmpresa.MEDIO,
        regime=RegimeTributario.LUCRO_PRESUMIDO,
        cnae_principal="4711302",
        uf="RJ",
        setor_macro=SetorMacro.COMERCIO,
    )
    diag = Diagnostico(
        tenant_id=tid,
        id=cid_d,
        empresa=empresa,
        respondente=Respondente(email="lead@teste.br", nome="Lead"),
    )
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14="33014556000196",
        payload_bruto={},
        payload_canonico={
            "cnpj": "33014556000196",
            "razao_social": "Razão Pública Consolidada LTDA",
        },
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    svc = MagicMock()
    svc.materializar_consulta = AsyncMock(return_value=mat)
    diag_repo = MagicMock()
    diag_repo.buscar_por_id = AsyncMock(return_value=diag)
    cnpj_repo = MagicMock()
    uc = ConsultarCnpjUseCase(service=svc, cnpj_repo=cnpj_repo, diagnostico_repo=diag_repo)
    cmd = ComandoConsultarCnpj(
        tenant_id=tid,
        cnpj_14="33014556000196",
        idempotency_key="k-merge",
        aplicar_no_diagnostico_id=cid_d,
        trace_id="t-abc",
    )
    out, aplicado = await uc.executar_e_materializar(cmd)
    assert aplicado is True
    assert out.consulta_id == mat.consulta_id
    cnpj_repo.atualizar_empresa_diagnostico_em_andamento.assert_called_once()
    kw = cnpj_repo.atualizar_empresa_diagnostico_em_andamento.call_args.kwargs
    assert kw["tenant_id"] == tid
    assert kw["diagnostico_id"] == cid_d
    assert kw["historico"][0][0] == "empresa_razao_social"
