"""Testes do calculador editorial PDCA / criticidade do plano materializado."""

from __future__ import annotations

import pytest

from src.domain.services.calculador_plano_acao import (
    chunk_id_sintetico_para_texto,
    computar_criticidade,
    criticidade_rotulo_pt_para_enum,
    fase_pdca_default_para_dimensao,
    inferir_horizonte_de_prazo_texto,
)
from src.domain.value_objects.plano_acao import (
    CriticidadePlanoAcao,
    FasePdcaPlano,
    HorizontePlanoAcao,
)
from src.domain.value_objects.score import Dimensao


class TestComputarCriticidade:
    """Faixas de severidade (ABNT 17301 cap. 6.1 — matriz interna)."""

    def test_gap_grande_em_fiscal_e_critica(self) -> None:
        c = computar_criticidade(10.0, 0.0, Dimensao.FISCAL.value)
        assert c is CriticidadePlanoAcao.CRITICA

    def test_desempenho_alto_reduz_criticidade(self) -> None:
        c = computar_criticidade(8.0, 0.95, Dimensao.ESTRATEGICA.value)
        assert c is CriticidadePlanoAcao.BAIXA

    def test_faixa_media(self) -> None:
        c = computar_criticidade(8.0, 0.5, Dimensao.ESTRATEGICA.value)
        assert c is CriticidadePlanoAcao.MEDIA

    def test_faixa_alta(self) -> None:
        c = computar_criticidade(10.0, 0.3, Dimensao.FISCAL.value)
        assert c is CriticidadePlanoAcao.ALTA

    def test_rejeita_dimensao_desconhecida(self) -> None:
        with pytest.raises(ValueError, match="Dimensão desconhecida"):
            computar_criticidade(5.0, 0.5, "fantasma")

    def test_rejeita_ratio_fora_intervalo(self) -> None:
        with pytest.raises(ValueError, match="ratio_resposta"):
            computar_criticidade(5.0, 1.5, Dimensao.FISCAL.value)

    def test_rejeita_peso_fora_intervalo(self) -> None:
        with pytest.raises(ValueError, match="peso_pergunta"):
            computar_criticidade(11.0, 0.5, Dimensao.FISCAL.value)


class TestFasePdcaDefault:
    def test_estrategica_plan(self) -> None:
        assert fase_pdca_default_para_dimensao(Dimensao.ESTRATEGICA.value) is FasePdcaPlano.PLAN

    def test_financeira_check(self) -> None:
        assert fase_pdca_default_para_dimensao(Dimensao.FINANCEIRA.value) is FasePdcaPlano.CHECK

    def test_compliance_act(self) -> None:
        assert fase_pdca_default_para_dimensao(Dimensao.COMPLIANCE_ABNT.value) is FasePdcaPlano.ACT

    def test_fiscal_do(self) -> None:
        assert fase_pdca_default_para_dimensao(Dimensao.FISCAL.value) is FasePdcaPlano.DO

    def test_none_retorna_do(self) -> None:
        assert fase_pdca_default_para_dimensao(None) is FasePdcaPlano.DO


class TestCriticidadeRotuloPt:
    def test_variacoes(self) -> None:
        assert criticidade_rotulo_pt_para_enum("Crítica") is CriticidadePlanoAcao.CRITICA
        assert criticidade_rotulo_pt_para_enum("ALTA") is CriticidadePlanoAcao.ALTA
        assert criticidade_rotulo_pt_para_enum("média") is CriticidadePlanoAcao.MEDIA
        assert criticidade_rotulo_pt_para_enum("baixa") is CriticidadePlanoAcao.BAIXA


class TestInferirHorizonte:
    def test_dias(self) -> None:
        assert inferir_horizonte_de_prazo_texto("30 dias") is HorizontePlanoAcao.IMEDIATO
        assert inferir_horizonte_de_prazo_texto("45 dias") is HorizontePlanoAcao.CURTO_PRAZO
        assert inferir_horizonte_de_prazo_texto("120 dias") is HorizontePlanoAcao.MEDIO_PRAZO

    def test_texto_editorial(self) -> None:
        assert (
            inferir_horizonte_de_prazo_texto("Longo prazo (24-36)")
            is HorizontePlanoAcao.LONGO_PRAZO
        )
        assert inferir_horizonte_de_prazo_texto("Médio prazo") is HorizontePlanoAcao.MEDIO_PRAZO
        assert (
            inferir_horizonte_de_prazo_texto("Curto prazo (0-12 meses)")
            is HorizontePlanoAcao.CURTO_PRAZO
        )

    def test_mes_ano(self) -> None:
        assert inferir_horizonte_de_prazo_texto("nov/2025") is HorizontePlanoAcao.CURTO_PRAZO

    def test_estrategico_por_96(self) -> None:
        assert inferir_horizonte_de_prazo_texto("96 meses") is HorizontePlanoAcao.ESTRATEGICO

    def test_padrao_curto(self) -> None:
        assert inferir_horizonte_de_prazo_texto("qualquer coisa") is HorizontePlanoAcao.CURTO_PRAZO


class TestChunkIdSintetico:
    def test_estavel(self) -> None:
        a = chunk_id_sintetico_para_texto("mesmo texto")
        b = chunk_id_sintetico_para_texto("mesmo texto")
        assert a == b
