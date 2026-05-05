"""Testes dos casos de uso de subtarefas do plano materializado."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.plano_painel_subtarefa import (
    AtualizarSubtarefaPlanoDiagnostico,
    ComandoAtualizarSubtarefaPlanoDiagnostico,
    ComandoCriarSubtarefaPlanoDiagnostico,
    CriarSubtarefaPlanoDiagnostico,
)


class TestCriarSubtarefaPlanoDiagnostico:
    async def test_executa_repo(self) -> None:
        repo = AsyncMock()
        repo.inserir_subtarefa_plano.return_value = {"id": "1", "titulo": "T"}
        uc = CriarSubtarefaPlanoDiagnostico(repo)
        tid, did, aid = uuid4(), uuid4(), uuid4()
        cmd = ComandoCriarSubtarefaPlanoDiagnostico(
            tenant_id=tid, diagnostico_id=did, plano_acao_id=aid, titulo="  Nova  ", ordem=2
        )
        out = await uc.execute(cmd)
        assert out["titulo"] == "T"
        repo.inserir_subtarefa_plano.assert_awaited_once_with(tid, did, aid, "Nova", 2)

    async def test_titulo_vazio(self) -> None:
        repo = AsyncMock()
        uc = CriarSubtarefaPlanoDiagnostico(repo)
        cmd = ComandoCriarSubtarefaPlanoDiagnostico(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            plano_acao_id=uuid4(),
            titulo="   ",
        )
        with pytest.raises(ValueError, match="obrigatório"):
            await uc.execute(cmd)


class TestAtualizarSubtarefaPlanoDiagnostico:
    async def test_executa_repo(self) -> None:
        repo = AsyncMock()
        repo.atualizar_subtarefa_plano.return_value = {"id": "1", "status": "feita"}
        uc = AtualizarSubtarefaPlanoDiagnostico(repo)
        tid, did, sid = uuid4(), uuid4(), uuid4()
        cmd = ComandoAtualizarSubtarefaPlanoDiagnostico(
            tenant_id=tid,
            diagnostico_id=did,
            subtarefa_id=sid,
            status="feita",
            prazo=date(2026, 5, 1),
        )
        out = await uc.execute(cmd)
        assert out["status"] == "feita"

    async def test_repo_retorna_none(self) -> None:
        repo = AsyncMock()
        repo.atualizar_subtarefa_plano.return_value = None
        uc = AtualizarSubtarefaPlanoDiagnostico(repo)
        cmd = ComandoAtualizarSubtarefaPlanoDiagnostico(
            tenant_id=uuid4(), diagnostico_id=uuid4(), subtarefa_id=uuid4(), titulo="x"
        )
        with pytest.raises(ValueError, match="não encontrada"):
            await uc.execute(cmd)
