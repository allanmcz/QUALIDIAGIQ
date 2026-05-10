"""Testes do caso de uso GerarExportPortabilidadeDiagnostico."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.ports.lgpd_titular_solicitacao_port import (
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    ComandoGerarExportPortabilidadeDiagnostico,
    GerarExportPortabilidadeDiagnostico,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


def _diag_exportavel(tenant_id: uuid.UUID, diag_id: uuid.UUID) -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(
        tenant_id=tenant_id,
        empresa=emp,
        respondente=Respondente(email="a@b.com"),
        id=diag_id,
    )
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=80.0, peso_total_aplicado=10.0),
        score_por_dimensao={
            Dimensao.FISCAL: ScoreNumerico(valor=80.0, peso_total_aplicado=10.0),
        },
    )
    d.finalizar_e_registrar_evidencia(sc)
    return d


@pytest.mark.asyncio
async def test_execute_sem_pdf_retorna_json_e_chama_validador() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)

    sol_port = AsyncMock()

    async def _buscar(**kwargs: object) -> MagicMock:
        m = MagicMock()
        m.diagnostico_id = diag_id
        m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
        m.status = StatusSolicitacaoTitular.DEFERIDA
        return m

    sol_port.buscar_por_id = AsyncMock(side_effect=_buscar)

    validado: list[bool] = []

    def validar(p: dict) -> None:
        validado.append(True)
        assert p["schema_id"] == "qdi-diagnostico-export-v1"

    pdf_chamado = False

    def gerar_pdf(jb: bytes, did: str, tid: str) -> bytes:
        nonlocal pdf_chamado
        pdf_chamado = True
        return b""

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=validar,
        gerar_pdf_com_anexo_json=gerar_pdf,
    )
    r = await uc.execute(
        ComandoGerarExportPortabilidadeDiagnostico(
            tenant_id=tenant_id,
            diagnostico_id=diag_id,
            solicitacao_id=sol_id,
            gerar_pdf_anexo=False,
        )
    )
    assert validado
    assert r.pdf_bytes is None
    assert not pdf_chamado
    assert b"schema_id" in r.json_utf8


@pytest.mark.asyncio
async def test_execute_com_pdf_chama_gerador() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    sol_port = AsyncMock()

    async def _buscar(**kwargs: object) -> MagicMock:
        m = MagicMock()
        m.diagnostico_id = diag_id
        m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
        m.status = StatusSolicitacaoTitular.DEFERIDA
        return m

    sol_port.buscar_por_id = AsyncMock(side_effect=_buscar)

    def validar(_p: dict) -> None:
        pass

    def gerar_pdf(jb: bytes, did: str, tid: str) -> bytes:
        assert jb.startswith(b"{")
        assert did == str(diag_id)
        assert tid == str(tenant_id)
        return b"%PDF-fake"

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=validar,
        gerar_pdf_com_anexo_json=gerar_pdf,
    )
    r = await uc.execute(
        ComandoGerarExportPortabilidadeDiagnostico(
            tenant_id=tenant_id,
            diagnostico_id=diag_id,
            solicitacao_id=sol_id,
            gerar_pdf_anexo=True,
        )
    )
    assert r.pdf_bytes == b"%PDF-fake"


async def _uc_erro_solicitacao(
    tenant_id: uuid.UUID,
    diag_id: uuid.UUID,
    sol_id: uuid.UUID,
    diag: Diagnostico,
    sol_mock: MagicMock | None,
) -> None:
    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    sol_port = AsyncMock()
    sol_port.buscar_por_id = AsyncMock(return_value=sol_mock)

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=lambda _p: None,
        gerar_pdf_com_anexo_json=lambda _j, _d, _t: b"",
    )
    with pytest.raises(ValueError):
        await uc.execute(
            ComandoGerarExportPortabilidadeDiagnostico(
                tenant_id=tenant_id,
                diagnostico_id=diag_id,
                solicitacao_id=sol_id,
                gerar_pdf_anexo=False,
            )
        )


@pytest.mark.asyncio
async def test_execute_solicitacao_nao_encontrada() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)
    await _uc_erro_solicitacao(tenant_id, diag_id, sol_id, diag, None)


@pytest.mark.asyncio
async def test_execute_solicitacao_diagnostico_diferente() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)
    m = MagicMock()
    m.diagnostico_id = uuid.uuid4()
    m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
    m.status = StatusSolicitacaoTitular.DEFERIDA
    await _uc_erro_solicitacao(tenant_id, diag_id, sol_id, diag, m)


@pytest.mark.asyncio
async def test_execute_solicitacao_tipo_incorreto() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)
    m = MagicMock()
    m.diagnostico_id = diag_id
    m.tipo = TipoSolicitacaoTitular.ANONIMIZACAO
    m.status = StatusSolicitacaoTitular.DEFERIDA
    await _uc_erro_solicitacao(tenant_id, diag_id, sol_id, diag, m)


@pytest.mark.asyncio
async def test_execute_solicitacao_nao_deferida() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()
    diag = _diag_exportavel(tenant_id, diag_id)
    m = MagicMock()
    m.diagnostico_id = diag_id
    m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
    m.status = StatusSolicitacaoTitular.RECEBIDA
    await _uc_erro_solicitacao(tenant_id, diag_id, sol_id, diag, m)


@pytest.mark.asyncio
async def test_execute_diagnostico_ausente() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=None)
    sol_port = AsyncMock()

    async def _buscar(**kwargs: object) -> MagicMock:
        m = MagicMock()
        m.diagnostico_id = diag_id
        m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
        m.status = StatusSolicitacaoTitular.DEFERIDA
        return m

    sol_port.buscar_por_id = AsyncMock(side_effect=_buscar)

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=lambda _p: None,
        gerar_pdf_com_anexo_json=lambda _j, _d, _t: b"",
    )
    with pytest.raises(ValueError, match="Diagnóstico não encontrado"):
        await uc.execute(
            ComandoGerarExportPortabilidadeDiagnostico(
                tenant_id=tenant_id,
                diagnostico_id=diag_id,
                solicitacao_id=sol_id,
                gerar_pdf_anexo=False,
            )
        )


@pytest.mark.asyncio
async def test_execute_diagnostico_nao_finalizado() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()

    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    diag = Diagnostico(
        tenant_id=tenant_id,
        empresa=emp,
        respondente=Respondente(email="a@b.com"),
        id=diag_id,
        status=StatusDiagnostico.EM_ANDAMENTO,
    )

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    sol_port = AsyncMock()

    async def _buscar(**kwargs: object) -> MagicMock:
        m = MagicMock()
        m.diagnostico_id = diag_id
        m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
        m.status = StatusSolicitacaoTitular.DEFERIDA
        return m

    sol_port.buscar_por_id = AsyncMock(side_effect=_buscar)

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=lambda _p: None,
        gerar_pdf_com_anexo_json=lambda _j, _d, _t: b"",
    )
    with pytest.raises(ValueError, match="finalizado"):
        await uc.execute(
            ComandoGerarExportPortabilidadeDiagnostico(
                tenant_id=tenant_id,
                diagnostico_id=diag_id,
                solicitacao_id=sol_id,
                gerar_pdf_anexo=False,
            )
        )


@pytest.mark.asyncio
async def test_execute_sem_hash_evidencia() -> None:
    tenant_id = uuid.uuid4()
    diag_id = uuid.uuid4()
    sol_id = uuid.uuid4()

    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    diag = Diagnostico(
        tenant_id=tenant_id,
        empresa=emp,
        respondente=Respondente(email="a@b.com"),
        id=diag_id,
    )
    diag.finalizar(50.0)

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    sol_port = AsyncMock()

    async def _buscar(**kwargs: object) -> MagicMock:
        m = MagicMock()
        m.diagnostico_id = diag_id
        m.tipo = TipoSolicitacaoTitular.PORTABILIDADE
        m.status = StatusSolicitacaoTitular.DEFERIDA
        return m

    sol_port.buscar_por_id = AsyncMock(side_effect=_buscar)

    uc = GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=sol_port,
        validar_payload_export_v1=lambda _p: None,
        gerar_pdf_com_anexo_json=lambda _j, _d, _t: b"",
    )
    with pytest.raises(ValueError, match="hash"):
        await uc.execute(
            ComandoGerarExportPortabilidadeDiagnostico(
                tenant_id=tenant_id,
                diagnostico_id=diag_id,
                solicitacao_id=sol_id,
                gerar_pdf_anexo=False,
            )
        )
