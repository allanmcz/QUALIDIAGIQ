"""Testes de entidades ``GapDetectado`` e ``ItemAcao``."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

import pytest

from src.domain.entities.plano_acao import GapDetectado, ItemAcao
from src.domain.value_objects.evidencia_lexiq import EvidenciaLexiq
from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
    StatusExecucaoAcao,
)


def _evid() -> EvidenciaLexiq:
    return EvidenciaLexiq(
        norma="LC 214/2025",
        dispositivo="art. 1º",
        versao="v1",
        vigencia_inicio=date(2026, 1, 1),
        vigencia_fim=None,
        chunk_id=uuid4(),
        citacao_texto="Trecho",
        score_similaridade=0.9,
    )


class TestGapDetectado:
    def test_ok(self) -> None:
        g = GapDetectado(
            pergunta_codigo="Q-1",
            pergunta_id=uuid4(),
            dimensao="fiscal",
            peso=5.0,
            pontos_obtidos=1.0,
            ratio=0.2,
        )
        assert g.ratio == 0.2

    def test_ratio_invalido(self) -> None:
        with pytest.raises(ValueError, match="ratio"):
            GapDetectado(
                pergunta_codigo="Q-1",
                pergunta_id=uuid4(),
                dimensao="fiscal",
                peso=5.0,
                pontos_obtidos=1.0,
                ratio=2.0,
            )

    def test_peso_invalido(self) -> None:
        with pytest.raises(ValueError, match="peso"):
            GapDetectado(
                pergunta_codigo="Q-1",
                pergunta_id=uuid4(),
                dimensao="fiscal",
                peso=11.0,
                pontos_obtidos=1.0,
                ratio=0.5,
            )


class TestItemAcao:
    def test_hash_automatico(self) -> None:
        hoje = datetime.now(UTC)
        i = ItemAcao(
            id=uuid4(),
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            codigo="ACAO-1",
            titulo="Título",
            descricao="D" * 10,
            dimensao="fiscal",
            fase_pdca=FasePdcaPlano.DO,
            horizonte=HorizontePlanoAcao.CURTO_PRAZO,
            criticidade=CriticidadePlanoAcao.ALTA,
            area_responsavel="Fiscal",
            peso_calculado=7.0,
            perguntas_origem=[uuid4()],
            evidencias=(_evid(),),
            criado_em=hoje,
        )
        assert len(i.hash_sha256) == 64

    def test_hash_externo_preservado(self) -> None:
        hoje = datetime.now(UTC)
        h = "a" * 64
        i = ItemAcao(
            id=uuid4(),
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            codigo="ACAO-1",
            titulo="Título",
            descricao="D" * 10,
            dimensao="fiscal",
            fase_pdca=FasePdcaPlano.DO,
            horizonte=HorizontePlanoAcao.CURTO_PRAZO,
            criticidade=CriticidadePlanoAcao.ALTA,
            area_responsavel="Fiscal",
            peso_calculado=7.0,
            perguntas_origem=[uuid4()],
            evidencias=(_evid(),),
            criado_em=hoje,
            hash_sha256=h,
        )
        assert i.hash_sha256 == h

    def test_rejeita_titulo_longo(self) -> None:
        hoje = datetime.now(UTC)
        with pytest.raises(ValueError, match="titulo"):
            ItemAcao(
                id=uuid4(),
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                codigo="ACAO-1",
                titulo="X" * 121,
                descricao="D",
                dimensao="fiscal",
                fase_pdca=FasePdcaPlano.DO,
                horizonte=HorizontePlanoAcao.CURTO_PRAZO,
                criticidade=CriticidadePlanoAcao.ALTA,
                area_responsavel="Fiscal",
                peso_calculado=7.0,
                perguntas_origem=[uuid4()],
                evidencias=(_evid(),),
                criado_em=hoje,
            )

    def test_rejeita_peso_calculado_invalido(self) -> None:
        hoje = datetime.now(UTC)
        with pytest.raises(ValueError, match="peso_calculado"):
            ItemAcao(
                id=uuid4(),
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                codigo="ACAO-1",
                titulo="T",
                descricao="D",
                dimensao="fiscal",
                fase_pdca=FasePdcaPlano.DO,
                horizonte=HorizontePlanoAcao.CURTO_PRAZO,
                criticidade=CriticidadePlanoAcao.ALTA,
                area_responsavel="Fiscal",
                peso_calculado=11.0,
                perguntas_origem=[uuid4()],
                evidencias=(_evid(),),
                criado_em=hoje,
            )

    def test_rejeita_descricao_longa(self) -> None:
        hoje = datetime.now(UTC)
        with pytest.raises(ValueError, match="descricao"):
            ItemAcao(
                id=uuid4(),
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                codigo="ACAO-1",
                titulo="T",
                descricao="D" * 2001,
                dimensao="fiscal",
                fase_pdca=FasePdcaPlano.DO,
                horizonte=HorizontePlanoAcao.CURTO_PRAZO,
                criticidade=CriticidadePlanoAcao.ALTA,
                area_responsavel="Fiscal",
                peso_calculado=7.0,
                perguntas_origem=[uuid4()],
                evidencias=(_evid(),),
                criado_em=hoje,
            )

    def test_rejeita_sem_evidencia(self) -> None:
        with pytest.raises(ValueError, match="evidência"):
            ItemAcao(
                id=uuid4(),
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                codigo="ACAO-1",
                titulo="T",
                descricao="D",
                dimensao="fiscal",
                fase_pdca=FasePdcaPlano.DO,
                horizonte=HorizontePlanoAcao.CURTO_PRAZO,
                criticidade=CriticidadePlanoAcao.ALTA,
                area_responsavel="Fiscal",
                peso_calculado=7.0,
                perguntas_origem=[],
                evidencias=(),
            )

    def test_prazo_meta_futuro_ok(self) -> None:
        hoje = datetime.now(UTC)
        amanha = (hoje + timedelta(days=1)).date()
        i = ItemAcao(
            id=uuid4(),
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            codigo="ACAO-1",
            titulo="T",
            descricao="D",
            dimensao="fiscal",
            fase_pdca=FasePdcaPlano.DO,
            horizonte=HorizontePlanoAcao.CURTO_PRAZO,
            criticidade=CriticidadePlanoAcao.ALTA,
            area_responsavel="Fiscal",
            peso_calculado=7.0,
            perguntas_origem=[uuid4()],
            evidencias=(_evid(),),
            prazo_meta=amanha,
            criado_em=hoje,
        )
        assert i.prazo_meta == amanha

    def test_rejeita_prazo_meta_passado(self) -> None:
        hoje = datetime.now(UTC)
        ontem = (hoje - timedelta(days=1)).date()
        with pytest.raises(ValueError, match="prazo_meta"):
            ItemAcao(
                id=uuid4(),
                tenant_id=uuid4(),
                diagnostico_id=uuid4(),
                codigo="ACAO-1",
                titulo="T",
                descricao="D",
                dimensao="fiscal",
                fase_pdca=FasePdcaPlano.DO,
                horizonte=HorizontePlanoAcao.CURTO_PRAZO,
                criticidade=CriticidadePlanoAcao.ALTA,
                area_responsavel="Fiscal",
                peso_calculado=7.0,
                perguntas_origem=[uuid4()],
                evidencias=(_evid(),),
                prazo_meta=ontem,
                criado_em=hoje,
            )

    def test_status_enum(self) -> None:
        hoje = datetime.now(UTC)
        i = ItemAcao(
            id=uuid4(),
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            codigo="ACAO-1",
            titulo="T",
            descricao="D",
            dimensao="fiscal",
            fase_pdca=FasePdcaPlano.DO,
            horizonte=HorizontePlanoAcao.CURTO_PRAZO,
            criticidade=CriticidadePlanoAcao.ALTA,
            area_responsavel="Fiscal",
            peso_calculado=7.0,
            perguntas_origem=[uuid4()],
            evidencias=(_evid(),),
            status=StatusExecucaoAcao.EM_ANDAMENTO,
            criado_em=hoje,
        )
        assert i.status is StatusExecucaoAcao.EM_ANDAMENTO
