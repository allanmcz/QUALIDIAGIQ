"""Testes do validador de recusa controlada (application)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from src.application.services.validador_recusa_controlada import ValidadorRecusaControlada
from src.domain.entities.plano_acao import ItemAcao
from src.domain.value_objects.evidencia_lexiq import EvidenciaLexiq
from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
)


def _item_com_evidencia(
    *,
    score: float = 0.9,
    vigencia_fim: date | None = None,
) -> ItemAcao:
    hoje = datetime.now(UTC)
    return ItemAcao(
        id=uuid4(),
        tenant_id=uuid4(),
        diagnostico_id=uuid4(),
        codigo="X",
        titulo="T",
        descricao="D",
        dimensao="fiscal",
        fase_pdca=FasePdcaPlano.DO,
        horizonte=HorizontePlanoAcao.CURTO_PRAZO,
        criticidade=CriticidadePlanoAcao.ALTA,
        area_responsavel="F",
        peso_calculado=5.0,
        perguntas_origem=[uuid4()],
        evidencias=(
            EvidenciaLexiq(
                norma="N",
                dispositivo="D",
                versao="v1",
                vigencia_inicio=date(2025, 1, 1),
                vigencia_fim=vigencia_fim,
                chunk_id=uuid4(),
                citacao_texto="Citação",
                score_similaridade=score,
            ),
        ),
        criado_em=hoje,
    )


class TestValidadorRecusaControlada:
    def test_aprovado(self) -> None:
        v = ValidadorRecusaControlada()
        r = v.validar(_item_com_evidencia())
        assert r.aprovado is True

    def test_rejeita_norma_fora_vigencia(self) -> None:
        v = ValidadorRecusaControlada()
        ontem = date.today() - timedelta(days=1)
        r = v.validar(_item_com_evidencia(vigencia_fim=ontem))
        assert r.aprovado is False
        assert r.motivo == "norma_fora_vigencia"

    def test_hoje_explicito(self) -> None:
        v = ValidadorRecusaControlada()
        futuro = date.today() + timedelta(days=30)
        item = _item_com_evidencia(vigencia_fim=futuro)
        r = v.validar(item, hoje=date.today())
        assert r.aprovado is True

    def test_sem_evidencia_mock(self) -> None:
        v = ValidadorRecusaControlada()
        item = MagicMock()
        item.codigo = "X"
        item.evidencias = ()
        r = v.validar(item)
        assert r.aprovado is False
        assert r.motivo == "sem_evidencia_lexiq"

    def test_similaridade_insuficiente_mock(self) -> None:
        v = ValidadorRecusaControlada()
        item = MagicMock()
        item.codigo = "X"
        ev = MagicMock()
        ev.score_similaridade = 0.5
        ev.vigencia_fim = None
        ev.norma = "N"
        item.evidencias = (ev,)
        r = v.validar(item)
        assert r.aprovado is False
        assert r.motivo == "similaridade_insuficiente"
