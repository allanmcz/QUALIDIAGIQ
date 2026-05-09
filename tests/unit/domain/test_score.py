import pytest

from src.domain.value_objects.score import (
    Dimensao,
    NivelMaturidade,
    PercentilSetorial,
    ScoreCompleto,
    ScoreNumerico,
    pesos_macro_dimensao_para_dict_iso,
)


class TestScoreNumerico:
    @pytest.mark.parametrize(
        "valor, peso_total",
        [
            (0.0, 10.0),
            (50.5, 15.5),
            (100.0, 100.0),
            (20.0, 0.0),
        ],
    )
    def test_deve_criar_score_numerico_valido(self, valor, peso_total):
        score = ScoreNumerico(valor=valor, peso_total_aplicado=peso_total)
        assert score.valor == valor
        assert score.peso_total_aplicado == peso_total
        assert score.perguntas_consideradas == ()

    @pytest.mark.parametrize("valor", [-0.1, -1.0, 100.1, 150.0])
    def test_deve_rejeitar_valor_invalido(self, valor):
        with pytest.raises(ValueError, match=r"Valor de score deve estar entre 0 e 100"):
            ScoreNumerico(valor=valor, peso_total_aplicado=10.0)

    def test_deve_rejeitar_peso_total_negativo(self):
        with pytest.raises(ValueError, match=r"Peso total aplicado não pode ser negativo"):
            ScoreNumerico(valor=50.0, peso_total_aplicado=-1.0)


class TestNivelMaturidade:
    @pytest.mark.parametrize(
        "score, nivel_esperado",
        [
            (0.0, NivelMaturidade.CRITICO),
            (20.0, NivelMaturidade.CRITICO),
            (20.1, NivelMaturidade.INICIAL),
            (40.0, NivelMaturidade.INICIAL),
            (40.1, NivelMaturidade.INTERMEDIARIO),
            (60.0, NivelMaturidade.INTERMEDIARIO),
            (60.1, NivelMaturidade.AVANCADO),
            (80.0, NivelMaturidade.AVANCADO),
            (80.1, NivelMaturidade.EXEMPLAR),
            (100.0, NivelMaturidade.EXEMPLAR),
        ],
    )
    def test_deve_converter_score_em_nivel_correto(self, score, nivel_esperado):
        assert NivelMaturidade.from_score(score) == nivel_esperado

    def test_nivel_via_score_numerico_property(self):
        score = ScoreNumerico(valor=45.0, peso_total_aplicado=10.0)
        assert score.nivel == NivelMaturidade.INTERMEDIARIO

    @pytest.mark.parametrize("score", [-1.0, 101.0])
    def test_deve_rejeitar_score_invalido_na_conversao(self, score):
        with pytest.raises(ValueError, match=r"Score inválido:"):
            NivelMaturidade.from_score(score)


class TestScoreCompleto:
    def test_deve_criar_score_completo_valido_com_uma_dimensao(self):
        score_geral = ScoreNumerico(valor=75.0, peso_total_aplicado=10.0)
        score_dimensao = ScoreNumerico(valor=75.0, peso_total_aplicado=10.0)
        score_por_dimensao = {Dimensao.FISCAL: score_dimensao}

        score_completo = ScoreCompleto(
            score_geral=score_geral,
            score_por_dimensao=score_por_dimensao,
        )

        assert score_completo.score_geral == score_geral
        assert score_completo.score_por_dimensao == score_por_dimensao
        assert score_completo.score_relativo_setor is None

    def test_deve_criar_score_completo_valido_com_multiplas_dimensoes(self):
        score_geral = ScoreNumerico(valor=60.0, peso_total_aplicado=20.0)
        score_fiscal = ScoreNumerico(valor=50.0, peso_total_aplicado=10.0)
        score_abnt = ScoreNumerico(valor=70.0, peso_total_aplicado=10.0)

        score_por_dimensao = {Dimensao.FISCAL: score_fiscal, Dimensao.COMPLIANCE_ABNT: score_abnt}

        score_completo = ScoreCompleto(
            score_geral=score_geral,
            score_por_dimensao=score_por_dimensao,
        )

        assert len(score_completo.score_por_dimensao) == 2

    def test_deve_rejeitar_score_completo_sem_dimensoes(self):
        score_geral = ScoreNumerico(valor=0.0, peso_total_aplicado=0.0)
        with pytest.raises(
            ValueError, match=r"ScoreCompleto deve conter ao menos uma dimensão avaliada\."
        ):
            ScoreCompleto(
                score_geral=score_geral,
                score_por_dimensao={},
            )


class TestPercentilSetorial:
    @pytest.mark.parametrize(
        "percentil, n_amostra",
        [
            (0, 1),
            (50, 10),
            (100, 1000),
        ],
    )
    def test_deve_criar_percentil_valido(self, percentil, n_amostra):
        ps = PercentilSetorial(
            percentil=percentil,
            setor_referencia="Comércio",
            porte_referencia="Médio",
            uf_referencia="SP",
            n_amostra=n_amostra,
        )
        assert ps.percentil == percentil
        assert ps.n_amostra == n_amostra

    @pytest.mark.parametrize("percentil", [-1, 101])
    def test_deve_rejeitar_percentil_invalido(self, percentil):
        with pytest.raises(ValueError, match=r"Percentil inválido:"):
            PercentilSetorial(
                percentil=percentil,
                setor_referencia="Varejo",
                porte_referencia="Pequeno",
                uf_referencia=None,
                n_amostra=10,
            )

    def test_deve_rejeitar_amostra_invalida(self):
        with pytest.raises(ValueError, match=r"n_amostra deve ser ≥ 1\."):
            PercentilSetorial(
                percentil=50,
                setor_referencia="Agro",
                porte_referencia="Grande",
                uf_referencia="MT",
                n_amostra=0,
            )


class TestPesosMacroDimensao:
    def test_pesos_macro_dimensao_para_dict_iso_cobre_todas_dimensoes(self) -> None:
        d = pesos_macro_dimensao_para_dict_iso()
        assert len(d) == len(Dimensao)
        assert d["fiscal"] == 1.5
        assert d["compliance_abnt_17301"] == 1.2


class TestScoreCompletoSerializacao:
    def test_para_dict_e_desde_dict_preserva_dados(self):
        sg = ScoreNumerico(valor=72.0, peso_total_aplicado=10.0, perguntas_consideradas=("Q-001",))
        sn_fiscal = ScoreNumerico(valor=80.0, peso_total_aplicado=5.0)
        original = ScoreCompleto(
            score_geral=sg,
            score_por_dimensao={Dimensao.FISCAL: sn_fiscal},
        )
        blob = original.para_dict_serializavel()
        reconstruido = ScoreCompleto.desde_dict(blob)
        assert reconstruido.score_geral.valor == original.score_geral.valor
        assert reconstruido.score_por_dimensao[Dimensao.FISCAL].valor == 80.0

    def test_para_dict_e_desde_dict_com_percentil_setorial(self) -> None:
        ps = PercentilSetorial(
            percentil=42,
            setor_referencia="Comércio",
            porte_referencia="Médio",
            uf_referencia="SP",
            n_amostra=100,
        )
        original = ScoreCompleto(
            score_geral=ScoreNumerico(valor=60.0, peso_total_aplicado=1.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=60.0, peso_total_aplicado=1.0),
            },
            score_relativo_setor=ps,
        )
        blob = original.para_dict_serializavel()
        assert blob["score_relativo_setor"]["percentil"] == 42
        reconstruido = ScoreCompleto.desde_dict(blob)
        assert reconstruido.score_relativo_setor is not None
        assert reconstruido.score_relativo_setor.percentil == 42
        assert reconstruido.score_relativo_setor.uf_referencia == "SP"
