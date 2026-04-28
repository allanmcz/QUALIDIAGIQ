import uuid

import pytest

from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro
from src.domain.entities.questionario import (
    CondicaoExibicao,
    Pergunta,
    Resposta,
    TipoPergunta,
)
from src.domain.value_objects.score import Dimensao


@pytest.fixture
def empresa_padrao():
    return EmpresaInfo(
        cnpj="12345678000199",
        razao_social="Empresa",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="123",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


@pytest.fixture
def empresa_lucro_real_industria():
    return EmpresaInfo(
        cnpj="12345678000199",
        razao_social="Indústria",
        porte=PorteEmpresa.GRANDE,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="123",
        uf="SP",
        setor_macro=SetorMacro.INDUSTRIA,
    )


class TestPergunta:
    def test_deve_rejeitar_pergunta_com_peso_negativo(self):
        with pytest.raises(ValueError, match=r"Peso não pode ser negativo"):
            Pergunta(
                codigo="Q-01",
                dimensao=Dimensao.FISCAL,
                texto="Teste",
                peso=-1.0,
                tipo=TipoPergunta.TERNARIA,
            )

    def test_pergunta_sem_condicao_deve_ser_aplicavel_a_todos(
        self, empresa_padrao, empresa_lucro_real_industria
    ):
        pergunta = Pergunta(
            codigo="Q-CORE",
            dimensao=Dimensao.FISCAL,
            texto="Pergunta Core",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
        )
        assert pergunta.aplicavel_para(empresa_padrao) is True
        assert pergunta.aplicavel_para(empresa_lucro_real_industria) is True

    def test_pergunta_exclusiva_lucro_real(self, empresa_padrao, empresa_lucro_real_industria):
        pergunta = Pergunta(
            codigo="Q-LR",
            dimensao=Dimensao.FISCAL,
            texto="Pergunta LR",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
            condicao=CondicaoExibicao(regimes_permitidos=(RegimeTributario.LUCRO_REAL,)),
        )
        # Falha para simples nacional
        assert pergunta.aplicavel_para(empresa_padrao) is False
        # Passa para lucro real
        assert pergunta.aplicavel_para(empresa_lucro_real_industria) is True

    def test_pergunta_exclusiva_industria(self, empresa_padrao, empresa_lucro_real_industria):
        pergunta = Pergunta(
            codigo="Q-IND",
            dimensao=Dimensao.OPERACIONAL,
            texto="Pergunta Indústria",
            peso=1.0,
            tipo=TipoPergunta.ESCALA_1_5,
            condicao=CondicaoExibicao(setores_permitidos=(SetorMacro.INDUSTRIA,)),
        )
        # Falha para comercio
        assert pergunta.aplicavel_para(empresa_padrao) is False
        # Passa para industria
        assert pergunta.aplicavel_para(empresa_lucro_real_industria) is True

    def test_pergunta_exclusiva_industria_e_lucro_real(self):
        empresa_industria_simples = EmpresaInfo(
            cnpj="12345678000199",
            razao_social="Indústria Simples",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="123",
            uf="SP",
            setor_macro=SetorMacro.INDUSTRIA,
        )

        pergunta = Pergunta(
            codigo="Q-COMPLEX",
            dimensao=Dimensao.FISCAL,
            texto="Pergunta Complexa",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
            condicao=CondicaoExibicao(
                regimes_permitidos=(RegimeTributario.LUCRO_REAL,),
                setores_permitidos=(SetorMacro.INDUSTRIA,),
            ),
        )

        # Falha pois é do setor certo, mas regime errado
        assert pergunta.aplicavel_para(empresa_industria_simples) is False


class TestResposta:
    @pytest.mark.parametrize(
        "valor_bruto, pontuacao_esperada",
        [("sim", 100.0), ("SIM", 100.0), ("parcialmente", 50.0), ("nao", 0.0), ("NAO", 0.0)],
    )
    def test_calculo_pontuacao_ternaria_valida(self, valor_bruto, pontuacao_esperada):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto=valor_bruto,
        )
        assert resposta.calcular_pontuacao() == pontuacao_esperada

    def test_calculo_pontuacao_ternaria_invalida(self):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto="talvez",
        )
        with pytest.raises(ValueError, match=r"Valor inválido para pergunta ternária"):
            resposta.calcular_pontuacao()

    @pytest.mark.parametrize(
        "valor_bruto, pontuacao_esperada",
        [(1, 0.0), ("1", 0.0), (2, 25.0), (3, 50.0), (4, 75.0), (5, 100.0), ("5", 100.0)],
    )
    def test_calculo_pontuacao_escala_valida(self, valor_bruto, pontuacao_esperada):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto=valor_bruto,
        )
        assert resposta.calcular_pontuacao() == pontuacao_esperada

    @pytest.mark.parametrize("valor_invalido", [0, 6, "6", -1])
    def test_calculo_pontuacao_escala_fora_limite(self, valor_invalido):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto=valor_invalido,
        )
        with pytest.raises(ValueError, match=r"Valor fora do limite da escala"):
            resposta.calcular_pontuacao()

    def test_calculo_pontuacao_escala_tipo_errado(self):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto="abc",
        )
        with pytest.raises(ValueError, match=r"Valor inválido para escala. Deve ser um número"):
            resposta.calcular_pontuacao()
