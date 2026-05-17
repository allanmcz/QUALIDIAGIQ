"""Testes unitários dos use cases do Kanban operacional."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.application.errors import DiagnosticoNaoEncontradoError
from src.application.ports.plano_acao_kanban_port import (
    AtualizarEstadoKanbanInput,
    PlanoAcaoComentarioRegistro,
    PlanoAcaoKanbanCard,
)
from src.application.use_cases.plano_acao_kanban import (
    AdicionarComentarioPlanoAcao,
    AtualizarEstadoOperacionalPlanoAcao,
    ComandoAdicionarComentarioPlanoAcao,
    ComandoAtualizarEstadoOperacionalPlanoAcao,
    ComandoListarKanbanPlanoAcao,
    ListarKanbanPlanoAcao,
    PlanoAcaoKanbanNaoEncontradoError,
)
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.status_execucao_plano_acao import StatusExecucaoPlanoAcao


def _card_fake(plano_id: UUID | None = None) -> PlanoAcaoKanbanCard:
    pid = plano_id or uuid4()
    return PlanoAcaoKanbanCard(
        plano_acao_id=pid,
        diagnostico_id=uuid4(),
        tenant_id=uuid4(),
        frente_indice=0,
        frente_nome="Fiscal",
        acao_indice=0,
        texto_acao="Ação teste",
        responsavel_sugerido="TI",
        prioridade_motor=1,
        criticidade="alta",
        base_legal="LC 214/2025",
        fase_pdca="plan",
        horizonte_planejado="curto",
        chave_quadro_legado="f0_a0",
        status_execucao=StatusExecucaoPlanoAcao.PENDENTE,
        responsavel_operacional=None,
        prazo_operacional=None,
        bloqueio_motivo=None,
        descricao_operacional=None,
        ordem_kanban=0,
        arquivado=False,
        comentarios_total=0,
        subtarefas_total=0,
    )


@pytest.mark.asyncio
class TestListarKanbanPlanoAcao:
    async def test_rejeita_diagnostico_inexistente(self) -> None:
        kanban = AsyncMock()
        repo = AsyncMock()
        repo.buscar_por_id.return_value = None
        uc = ListarKanbanPlanoAcao(kanban=kanban, diagnostico_repo=repo)
        did = uuid4()
        with pytest.raises(DiagnosticoNaoEncontradoError):
            await uc.execute(
                ComandoListarKanbanPlanoAcao(tenant_id=uuid4(), diagnostico_id=did)
            )
        kanban.listar_board.assert_not_called()


@pytest.mark.asyncio
class TestAtualizarEstadoOperacionalPlanoAcao:
    async def test_bloqueado_exige_motivo(self) -> None:
        kanban = AsyncMock()
        repo = AsyncMock()
        repo.buscar_por_id.return_value = AsyncMock(spec=Diagnostico)
        kanban.plano_acao_pertence_diagnostico.return_value = True
        uc = AtualizarEstadoOperacionalPlanoAcao(kanban=kanban, diagnostico_repo=repo)
        with pytest.raises(ValueError, match="bloqueio_motivo"):
            await uc.execute(
                ComandoAtualizarEstadoOperacionalPlanoAcao(
                    tenant_id=uuid4(),
                    diagnostico_id=uuid4(),
                    plano_acao_id=uuid4(),
                    dados=AtualizarEstadoKanbanInput(
                        status_execucao=StatusExecucaoPlanoAcao.BLOQUEADO
                    ),
                )
            )


@pytest.mark.asyncio
class TestAdicionarComentarioPlanoAcao:
    async def test_calcula_hash_antes_do_insert(self) -> None:
        kanban = AsyncMock()
        repo = AsyncMock()
        repo.buscar_por_id.return_value = AsyncMock(spec=Diagnostico)
        kanban.plano_acao_pertence_diagnostico.return_value = True
        plano_id = uuid4()
        tid = uuid4()
        did = uuid4()
        registro = PlanoAcaoComentarioRegistro(
            id=uuid4(),
            plano_acao_id=plano_id,
            diagnostico_id=did,
            tenant_id=tid,
            autor_label="Consultor",
            autor_email=None,
            autor_user_id=None,
            comentario="ok",
            sha256_payload="a" * 64,
            criado_em=datetime.now(UTC),
        )
        kanban.inserir_comentario.return_value = registro
        uc = AdicionarComentarioPlanoAcao(kanban=kanban, diagnostico_repo=repo)
        out = await uc.execute(
            ComandoAdicionarComentarioPlanoAcao(
                tenant_id=tid,
                diagnostico_id=did,
                plano_acao_id=plano_id,
                autor_label="Consultor",
                autor_email=None,
                autor_user_id=None,
                comentario="ok",
            )
        )
        assert out.comentario == "ok"
        call_kw = kanban.inserir_comentario.await_args.kwargs
        assert len(call_kw["sha256_payload"]) == 64

    async def test_plano_inexistente(self) -> None:
        kanban = AsyncMock()
        repo = AsyncMock()
        repo.buscar_por_id.return_value = AsyncMock(spec=Diagnostico)
        kanban.plano_acao_pertence_diagnostico.return_value = False
        uc = AdicionarComentarioPlanoAcao(kanban=kanban, diagnostico_repo=repo)
        with pytest.raises(PlanoAcaoKanbanNaoEncontradoError):
            await uc.execute(
                ComandoAdicionarComentarioPlanoAcao(
                    tenant_id=uuid4(),
                    diagnostico_id=uuid4(),
                    plano_acao_id=uuid4(),
                    autor_label="X",
                    autor_email=None,
                    autor_user_id=None,
                    comentario="texto",
                )
            )
