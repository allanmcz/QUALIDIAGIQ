"""Testes do caso de uso de backfill de respostas materializadas."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.use_cases.backfill_respostas_questionario import (
    BackfillRespostasQuestionario,
    ComandoBackfillRespostasQuestionario,
)


class TestBackfillRespostasQuestionario:
    @pytest.mark.asyncio
    async def test_sem_fonte_quando_rascunho_ausente(self) -> None:
        did = uuid4()
        tid = uuid4()

        async def listar(tenant_id, *, limite: int):
            assert tenant_id == tid
            return [{"id": did, "tenant_id": tid}]

        async def buscar(_did, _tid, *, janela_horas: int):
            return None

        async def persistir(*_a, **_k):
            return True

        uc = BackfillRespostasQuestionario(
            listar_sem_respostas=listar,
            buscar_payload_rascunho=buscar,
            persistir_linhas=persistir,
        )
        r = await uc.execute(ComandoBackfillRespostasQuestionario(tenant_id=tid, limite=10))
        assert r.processados == 1
        assert r.sem_fonte == 1
        assert r.preenchidos == 0
