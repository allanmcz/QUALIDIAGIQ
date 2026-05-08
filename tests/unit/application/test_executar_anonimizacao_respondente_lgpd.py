"""Testes do caso de uso de anonimização respondente pós-deferimento LGPD."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.application.ports.lgpd_anonimizacao_executor_port import (
    LgpdAnonimizacaoExecutorPort,
)
from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ComandoExecutarAnonimizacaoRespondenteLgpd,
    ExecutarAnonimizacaoRespondenteLgpd,
)


class _FakePort(LgpdTitularSolicitacaoPort):
    def __init__(self, row: SolicitacaoTitular | None) -> None:
        self._row = row

    async def criar(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID | None,
        tipo: TipoSolicitacaoTitular,
        canal: CanalSolicitacaoTitular,
        solicitante_email: str,
        payload: dict[str, Any],
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular:
        raise NotImplementedError

    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        status: StatusSolicitacaoTitular | None,
        limit: int,
    ) -> list[SolicitacaoTitular]:
        raise NotImplementedError

    async def buscar_por_id(
        self, *, tenant_id: UUID, solicitacao_id: UUID
    ) -> SolicitacaoTitular | None:
        if self._row is None:
            return None
        if self._row.tenant_id != tenant_id or self._row.id != solicitacao_id:
            return None
        return self._row

    async def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
        status: StatusSolicitacaoTitular,
        observacao_interna: str | None,
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular | None:
        raise NotImplementedError


class _RecordingExecutor(LgpdAnonimizacaoExecutorPort):
    def __init__(self) -> None:
        self.calls: list[tuple[UUID, UUID, UUID, UUID]] = []

    async def aplicar_anonimizacao_respondente(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        solicitacao_id: UUID,
        actor_user_id: UUID,
    ) -> None:
        self.calls.append((tenant_id, diagnostico_id, solicitacao_id, actor_user_id))


def _sol(
    *,
    tenant_id: UUID,
    solicitacao_id: UUID,
    diagnostico_id: UUID,
    tipo: TipoSolicitacaoTitular = TipoSolicitacaoTitular.ANONIMIZACAO,
    status: StatusSolicitacaoTitular = StatusSolicitacaoTitular.DEFERIDA,
) -> SolicitacaoTitular:
    now = datetime.now(UTC)
    return SolicitacaoTitular(
        id=solicitacao_id,
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        tipo=tipo,
        status=status,
        canal=CanalSolicitacaoTitular.PLATAFORMA,
        solicitante_email="t@ex.com",
        payload={},
        observacao_interna=None,
        actor_user_id=None,
        criado_em=now,
        atualizado_em=now,
    )


class TestExecutarAnonimizacaoRespondenteLgpd:
    @pytest.mark.asyncio
    async def test_executor_chamado_quando_valido(self) -> None:
        tenant = uuid4()
        sol_id = uuid4()
        diag_id = uuid4()
        actor = uuid4()
        row = _sol(tenant_id=tenant, solicitacao_id=sol_id, diagnostico_id=diag_id)
        port = _FakePort(row)
        ex = _RecordingExecutor()
        uc = ExecutarAnonimizacaoRespondenteLgpd(port_solicitacoes=port, executor=ex)
        cmd = ComandoExecutarAnonimizacaoRespondenteLgpd(
            tenant_id=tenant,
            actor_user_id=actor,
            diagnostico_id=diag_id,
            solicitacao_id=sol_id,
        )
        await uc.execute(cmd)
        assert ex.calls == [(tenant, diag_id, sol_id, actor)]

    @pytest.mark.asyncio
    async def test_rejeita_tipo_errado(self) -> None:
        tenant = uuid4()
        row = replace(
            _sol(tenant_id=tenant, solicitacao_id=uuid4(), diagnostico_id=uuid4()),
            tipo=TipoSolicitacaoTitular.ACESSO,
        )
        uc = ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=_FakePort(row), executor=_RecordingExecutor()
        )
        with pytest.raises(ValueError, match="anonimização"):
            await uc.execute(
                ComandoExecutarAnonimizacaoRespondenteLgpd(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    diagnostico_id=row.diagnostico_id or uuid4(),
                    solicitacao_id=row.id,
                )
            )

    @pytest.mark.asyncio
    async def test_rejeita_status_nao_deferida(self) -> None:
        tenant = uuid4()
        row = replace(
            _sol(tenant_id=tenant, solicitacao_id=uuid4(), diagnostico_id=uuid4()),
            status=StatusSolicitacaoTitular.EM_ANALISE,
        )
        uc = ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=_FakePort(row), executor=_RecordingExecutor()
        )
        with pytest.raises(ValueError, match="deferida"):
            await uc.execute(
                ComandoExecutarAnonimizacaoRespondenteLgpd(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    diagnostico_id=row.diagnostico_id or uuid4(),
                    solicitacao_id=row.id,
                )
            )

    @pytest.mark.asyncio
    async def test_rejeita_diag_divergente(self) -> None:
        tenant = uuid4()
        row = _sol(tenant_id=tenant, solicitacao_id=uuid4(), diagnostico_id=uuid4())
        uc = ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=_FakePort(row), executor=_RecordingExecutor()
        )
        with pytest.raises(ValueError, match="diverge"):
            await uc.execute(
                ComandoExecutarAnonimizacaoRespondenteLgpd(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    diagnostico_id=uuid4(),
                    solicitacao_id=row.id,
                )
            )

    @pytest.mark.asyncio
    async def test_rejeita_solicitacao_inexistente(self) -> None:
        tenant = uuid4()
        uc = ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=_FakePort(None), executor=_RecordingExecutor()
        )
        with pytest.raises(ValueError, match="não encontrada"):
            await uc.execute(
                ComandoExecutarAnonimizacaoRespondenteLgpd(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    diagnostico_id=uuid4(),
                    solicitacao_id=uuid4(),
                )
            )

    @pytest.mark.asyncio
    async def test_rejeita_sem_diagnostico_vinculado(self) -> None:
        tenant = uuid4()
        sol_id = uuid4()
        row = replace(
            _sol(tenant_id=tenant, solicitacao_id=sol_id, diagnostico_id=uuid4()),
            diagnostico_id=None,
        )
        uc = ExecutarAnonimizacaoRespondenteLgpd(
            port_solicitacoes=_FakePort(row), executor=_RecordingExecutor()
        )
        with pytest.raises(ValueError, match="vinculado"):
            await uc.execute(
                ComandoExecutarAnonimizacaoRespondenteLgpd(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    diagnostico_id=uuid4(),
                    solicitacao_id=sol_id,
                )
            )
