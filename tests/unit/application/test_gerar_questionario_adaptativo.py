import pytest

from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro
from src.domain.entities.questionario import CondicaoExibicao, Pergunta, TipoPergunta
from src.domain.value_objects.score import Dimensao


@pytest.fixture
def banco_perguntas_mock():
    return [
        Pergunta(
            codigo="Q-CORE",
            dimensao=Dimensao.FISCAL,
            texto="Pergunta de Nucleo (Todos)",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
        ),
        Pergunta(
            codigo="Q-LR",
            dimensao=Dimensao.CONTABIL,
            texto="Apenas Lucro Real",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
            condicao=CondicaoExibicao(regimes_permitidos=(RegimeTributario.LUCRO_REAL,)),
        ),
        Pergunta(
            codigo="Q-IND",
            dimensao=Dimensao.OPERACIONAL,
            texto="Apenas Industria",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
            condicao=CondicaoExibicao(setores_permitidos=(SetorMacro.INDUSTRIA,)),
        ),
    ]


class TestGerarQuestionarioAdaptativoUseCase:
    def test_deve_retornar_apenas_perguntas_core_para_comercio_simples(self, banco_perguntas_mock):
        use_case = GerarQuestionarioAdaptativoUseCase(banco_perguntas_mock)
        empresa = EmpresaInfo(
            cnpj="12345678000195",
            razao_social="Loja",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )

        perguntas = use_case.execute(empresa)
        assert len(perguntas) == 1
        assert perguntas[0].codigo == "Q-CORE"

    def test_deve_retornar_core_e_industria_para_industria_simples(self, banco_perguntas_mock):
        use_case = GerarQuestionarioAdaptativoUseCase(banco_perguntas_mock)
        empresa = EmpresaInfo(
            cnpj="12345678000195",
            razao_social="Fábrica",
            porte=PorteEmpresa.PEQUENO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.INDUSTRIA,
        )

        perguntas = use_case.execute(empresa)
        assert len(perguntas) == 2
        codigos = [p.codigo for p in perguntas]
        assert "Q-CORE" in codigos
        assert "Q-IND" in codigos

    def test_deve_retornar_todas_para_industria_lucro_real(self, banco_perguntas_mock):
        use_case = GerarQuestionarioAdaptativoUseCase(banco_perguntas_mock)
        empresa = EmpresaInfo(
            cnpj="12345678000195",
            razao_social="Mega Fábrica",
            porte=PorteEmpresa.GRANDE,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.INDUSTRIA,
        )

        perguntas = use_case.execute(empresa)
        assert len(perguntas) == 3
