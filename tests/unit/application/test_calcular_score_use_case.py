import uuid
from datetime import date

import pytest

from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
from src.domain.entities.questionario import Pergunta, Resposta, TipoPergunta
from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.embutidas_normativa_score_macro_repository import (
    EmbutidasNormativaScoreMacroRepository,
)


def _motor_padrao() -> CalcularScoreUseCase:
    return CalcularScoreUseCase(normativa_repo=EmbutidasNormativaScoreMacroRepository())


@pytest.fixture
def perguntas_mock():
    return [
        Pergunta(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            codigo="Q-FISC-001",
            dimensao=Dimensao.FISCAL,
            texto="Fiscal 1",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
        ),
        Pergunta(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            codigo="Q-TEC-001",
            dimensao=Dimensao.TECNOLOGICA,
            texto="Tec 1",
            peso=2.0,
            tipo=TipoPergunta.ESCALA_1_5,
        ),
    ]


class _RepoMacroIncompleto(NormativaScoreMacroRepository):
    def obter_pesos_macro_validos_na_data(self, data_referencia: date) -> dict[Dimensao, float]:
        _ = data_referencia
        return {Dimensao.FISCAL: 1.5}


class TestCalcularScoreUseCase:
    def test_deve_calcular_score_com_sucesso(self, perguntas_mock):
        use_case = _motor_padrao()

        diag_id = uuid.uuid4()
        respostas = [
            Resposta(
                diagnostico_id=diag_id,
                pergunta_id=perguntas_mock[0].id,
                pergunta_tipo=perguntas_mock[0].tipo,
                valor_bruto="sim",  # 100 pontos
            ),
            Resposta(
                diagnostico_id=diag_id,
                pergunta_id=perguntas_mock[1].id,
                pergunta_tipo=perguntas_mock[1].tipo,
                valor_bruto=3,  # 50 pontos
            ),
        ]

        score_completo = use_case.execute(
            perguntas=perguntas_mock,
            respostas=respostas,
            data_referencia_normativa=date(2026, 5, 1),
        )

        # Valida score Fiscal
        score_fiscal = score_completo.score_por_dimensao[Dimensao.FISCAL]
        assert score_fiscal.valor == 100.0  # 100 * 1.0 / 1.0
        assert score_fiscal.peso_total_aplicado == 1.0

        # Valida score Tecnologico
        score_tec = score_completo.score_por_dimensao[Dimensao.TECNOLOGICA]
        assert score_tec.valor == 50.0  # 50 * 2.0 / 2.0
        assert score_tec.peso_total_aplicado == 2.0

        # Valida score geral (pesos macro: Fiscal=1.5, Tec=1.3)
        # soma_pontos = (100.0 * 1.5) + (50.0 * 1.3) = 150 + 65 = 215
        # pesos = 1.5 + 1.3 = 2.8
        # geral = 215 / 2.8 = 76.785...
        assert score_completo.score_geral.valor == 76.79

    def test_deve_rejeitar_calculo_sem_respostas(self, perguntas_mock):
        use_case = _motor_padrao()
        with pytest.raises(ValueError, match=r"Não é possível calcular score sem respostas"):
            use_case.execute(perguntas=perguntas_mock, respostas=[])

    def test_deve_rejeitar_se_pergunta_nao_existir(self, perguntas_mock):
        use_case = _motor_padrao()
        respostas = [
            Resposta(
                diagnostico_id=uuid.uuid4(),
                pergunta_id=uuid.uuid4(),  # ID inexistente
                pergunta_tipo=TipoPergunta.TERNARIA,
                valor_bruto="sim",
            )
        ]
        with pytest.raises(ValueError, match=r"não encontrada no banco"):
            use_case.execute(perguntas=perguntas_mock, respostas=respostas)

    def test_nao_se_aplica_exclui_da_media_dimensao(self, perguntas_mock):
        """Doc 05_QUESTIONARIO §11.1 — excluir da média ponderada."""
        use_case = _motor_padrao()
        diag_id = uuid.uuid4()
        respostas = [
            Resposta(
                diagnostico_id=diag_id,
                pergunta_id=perguntas_mock[0].id,
                pergunta_tipo=perguntas_mock[0].tipo,
                valor_bruto="nao_se_aplica",
            ),
            Resposta(
                diagnostico_id=diag_id,
                pergunta_id=perguntas_mock[1].id,
                pergunta_tipo=perguntas_mock[1].tipo,
                valor_bruto=5,
            ),
        ]
        score = use_case.execute(perguntas=perguntas_mock, respostas=respostas)
        assert Dimensao.FISCAL not in score.score_por_dimensao
        assert score.score_por_dimensao[Dimensao.TECNOLOGICA].valor == 100.0

    def test_rejeita_mapa_macro_incompleto(self, perguntas_mock):
        use_case = CalcularScoreUseCase(normativa_repo=_RepoMacroIncompleto())
        diag_id = uuid.uuid4()
        respostas = [
            Resposta(
                diagnostico_id=diag_id,
                pergunta_id=perguntas_mock[0].id,
                pergunta_tipo=perguntas_mock[0].tipo,
                valor_bruto="sim",
            ),
        ]
        with pytest.raises(ValueError, match=r"falta a dimensão"):
            use_case.execute(perguntas=perguntas_mock, respostas=respostas)
