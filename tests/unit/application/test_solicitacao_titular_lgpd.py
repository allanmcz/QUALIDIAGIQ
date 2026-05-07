"""Tests dos casos de uso LGPD (solicitações do titular)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    LgpdTitularSolicitacaoPort,
    SolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.application.use_cases.atualizar_status_solicitacao_titular_lgpd import (
    AtualizarStatusSolicitacaoTitularLgpd,
    ComandoAtualizarStatusSolicitacaoTitularLgpd,
)
from src.application.use_cases.listar_solicitacao_titular_lgpd import (
    ComandoListarSolicitacaoTitularLgpd,
    ListarSolicitacaoTitularLgpd,
)
from src.application.use_cases.registrar_solicitacao_titular_lgpd import (
    ComandoRegistrarSolicitacaoTitularLgpd,
    RegistrarSolicitacaoTitularLgpd,
)


class FakeLgpdTitularSolicitacaoPort(LgpdTitularSolicitacaoPort):
    """Fake em memória para testes unitários dos casos de uso."""

    def __init__(self) -> None:
        self._rows: list[SolicitacaoTitular] = []

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
        now = datetime.now(UTC)
        row = SolicitacaoTitular(
            id=uuid4(),
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            tipo=tipo,
            status=StatusSolicitacaoTitular.RECEBIDA,
            canal=canal,
            solicitante_email=solicitante_email,
            payload=payload,
            observacao_interna=None,
            actor_user_id=actor_user_id,
            criado_em=now,
            atualizado_em=now,
        )
        self._rows.append(row)
        return row

    async def listar_por_tenant(
        self,
        *,
        tenant_id: UUID,
        status: StatusSolicitacaoTitular | None,
        limit: int,
    ) -> list[SolicitacaoTitular]:
        rows = [r for r in self._rows if r.tenant_id == tenant_id]
        if status is not None:
            rows = [r for r in rows if r.status == status]
        return rows[:limit]

    async def atualizar_status(
        self,
        *,
        tenant_id: UUID,
        solicitacao_id: UUID,
        status: StatusSolicitacaoTitular,
        observacao_interna: str | None,
        actor_user_id: UUID | None,
    ) -> SolicitacaoTitular | None:
        for idx, row in enumerate(self._rows):
            if row.tenant_id == tenant_id and row.id == solicitacao_id:
                updated = replace(
                    row,
                    status=status,
                    observacao_interna=observacao_interna,
                    actor_user_id=actor_user_id,
                    atualizado_em=datetime.now(UTC),
                )
                self._rows[idx] = updated
                return updated
        return None


class TestSolicitacaoTitularLgpdUseCases:
    """Cobertura de criação, listagem e atualização de status."""

    @pytest.mark.asyncio
    async def test_registrar_normaliza_email(self) -> None:
        port = FakeLgpdTitularSolicitacaoPort()
        use_case = RegistrarSolicitacaoTitularLgpd(port=port)
        tenant_id = uuid4()

        created = await use_case.execute(
            ComandoRegistrarSolicitacaoTitularLgpd(
                tenant_id=tenant_id,
                diagnostico_id=None,
                tipo=TipoSolicitacaoTitular.ACESSO,
                canal=CanalSolicitacaoTitular.PLATAFORMA,
                solicitante_email="  ALLAN@Empresa.COM ",
                payload={"motivo": "acesso"},
            )
        )

        assert created.tenant_id == tenant_id
        assert created.solicitante_email == "allan@empresa.com"
        assert created.status == StatusSolicitacaoTitular.RECEBIDA

    @pytest.mark.asyncio
    async def test_listar_com_filtro_status(self) -> None:
        port = FakeLgpdTitularSolicitacaoPort()
        tenant_id = uuid4()
        other_tenant = uuid4()
        reg = RegistrarSolicitacaoTitularLgpd(port=port)
        upd = AtualizarStatusSolicitacaoTitularLgpd(port=port)
        lst = ListarSolicitacaoTitularLgpd(port=port)

        row1 = await reg.execute(
            ComandoRegistrarSolicitacaoTitularLgpd(
                tenant_id=tenant_id,
                diagnostico_id=None,
                tipo=TipoSolicitacaoTitular.PORTABILIDADE,
                canal=CanalSolicitacaoTitular.SELF_SERVICE,
                solicitante_email="a@empresa.com",
                payload={},
            )
        )
        await reg.execute(
            ComandoRegistrarSolicitacaoTitularLgpd(
                tenant_id=other_tenant,
                diagnostico_id=None,
                tipo=TipoSolicitacaoTitular.ACESSO,
                canal=CanalSolicitacaoTitular.PLATAFORMA,
                solicitante_email="b@empresa.com",
                payload={},
            )
        )
        await upd.execute(
            ComandoAtualizarStatusSolicitacaoTitularLgpd(
                tenant_id=tenant_id,
                solicitacao_id=row1.id,
                status=StatusSolicitacaoTitular.EM_ANALISE,
                observacao_interna="triagem",
            )
        )

        filtradas = await lst.execute(
            ComandoListarSolicitacaoTitularLgpd(
                tenant_id=tenant_id,
                status=StatusSolicitacaoTitular.EM_ANALISE,
                limit=20,
            )
        )
        assert len(filtradas) == 1
        assert filtradas[0].id == row1.id

    @pytest.mark.asyncio
    async def test_atualizar_status_retorna_none_quando_nao_encontra(self) -> None:
        port = FakeLgpdTitularSolicitacaoPort()
        use_case = AtualizarStatusSolicitacaoTitularLgpd(port=port)

        updated = await use_case.execute(
            ComandoAtualizarStatusSolicitacaoTitularLgpd(
                tenant_id=uuid4(),
                solicitacao_id=uuid4(),
                status=StatusSolicitacaoTitular.INDEFERIDA,
                observacao_interna="sem vínculo",
            )
        )
        assert updated is None
