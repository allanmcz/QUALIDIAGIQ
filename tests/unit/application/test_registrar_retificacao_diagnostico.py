"""Testes de RegistrarRetificacaoDiagnostico."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.application.use_cases.registrar_retificacao_diagnostico import (
    ComandoRegistrarRetificacaoDiagnostico,
    RegistrarRetificacaoDiagnostico,
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


def _diag_finalizado_com_hash(tenant_id: uuid.UUID) -> Diagnostico:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(tenant_id=tenant_id, empresa=emp, respondente=Respondente(email="a@b.com"))
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
        score_por_dimensao={
            Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
        },
    )
    d.finalizar_e_registrar_evidencia(sc)
    return d


@pytest.mark.asyncio
async def test_execute_insere_retificacao() -> None:
    tenant_id = uuid.uuid4()
    actor = uuid.uuid4()
    tid = tenant_id
    diag = _diag_finalizado_com_hash(tenant_id)

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)

    ret_port = AsyncMock()
    ret_port.inserir = AsyncMock()

    now_id = uuid.uuid4()
    ret_port.inserir.return_value = DiagnosticoRetificacaoRegisto(
        id=now_id,
        tenant_id=tid,
        diagnostico_original_id=diag.id,
        hash_diagnostico_original_sha256="aa" * 32,
        motivo_retificacao="Correção após revisão documental",
        payload_retificacao={"k": 1},
        hash_retificacao_sha256="bb" * 32,
        actor_user_id=actor,
        criado_em=diag.finalizado_em or diag.criado_em or datetime.now(UTC),
    )

    uc = RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret_port)
    out = await uc.execute(
        ComandoRegistrarRetificacaoDiagnostico(
            tenant_id=tid,
            actor_user_id=actor,
            diagnostico_original_id=diag.id,
            motivo_retificacao="Correção após revisão documental",
            payload_retificacao={"k": 1},
        )
    )
    assert out.id == now_id
    ret_port.inserir.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_diagnostico_inexistente() -> None:
    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=None)
    ret_port = AsyncMock()
    uc = RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret_port)

    with pytest.raises(ValueError, match="não encontrado"):
        await uc.execute(
            ComandoRegistrarRetificacaoDiagnostico(
                tenant_id=uuid.uuid4(),
                actor_user_id=uuid.uuid4(),
                diagnostico_original_id=uuid.uuid4(),
                motivo_retificacao="Motivo longo o suficiente para validação",
                payload_retificacao={},
            )
        )


@pytest.mark.asyncio
async def test_execute_rejeita_nao_finalizado() -> None:
    tenant_id = uuid.uuid4()
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
        status=StatusDiagnostico.EM_ANDAMENTO,
    )

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    ret_port = AsyncMock()
    uc = RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret_port)

    with pytest.raises(ValueError, match="finalizado"):
        await uc.execute(
            ComandoRegistrarRetificacaoDiagnostico(
                tenant_id=tenant_id,
                actor_user_id=uuid.uuid4(),
                diagnostico_original_id=diag.id,
                motivo_retificacao="Motivo longo o suficiente para validação",
                payload_retificacao={},
            )
        )


@pytest.mark.asyncio
async def test_execute_rejeita_sem_hash_evidencia() -> None:
    tenant_id = uuid.uuid4()
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    diag = Diagnostico(tenant_id=tenant_id, empresa=emp, respondente=Respondente(email="a@b.com"))
    diag.finalizar(40.0)

    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(return_value=diag)
    ret_port = AsyncMock()
    uc = RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret_port)

    with pytest.raises(ValueError, match="hash"):
        await uc.execute(
            ComandoRegistrarRetificacaoDiagnostico(
                tenant_id=tenant_id,
                actor_user_id=uuid.uuid4(),
                diagnostico_original_id=diag.id,
                motivo_retificacao="Motivo longo o suficiente para validação",
                payload_retificacao={},
            )
        )
