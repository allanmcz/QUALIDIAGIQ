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
        cnpj="12345678000195",
        razao_social="Empresa",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


@pytest.fixture
def empresa_lucro_real_industria():
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Indústria",
        porte=PorteEmpresa.GRANDE,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.INDUSTRIA,
    )


@pytest.fixture
def pergunta_ternaria() -> Pergunta:
    return Pergunta(
        codigo="Q-T",
        dimensao=Dimensao.FISCAL,
        texto="Ternária",
        peso=1.0,
        tipo=TipoPergunta.TERNARIA,
    )


@pytest.fixture
def pergunta_escala() -> Pergunta:
    return Pergunta(
        codigo="Q-E",
        dimensao=Dimensao.FISCAL,
        texto="Escala",
        peso=1.0,
        tipo=TipoPergunta.ESCALA_1_5,
    )


@pytest.fixture
def pergunta_binaria() -> Pergunta:
    return Pergunta(
        codigo="Q-B",
        dimensao=Dimensao.FISCAL,
        texto="Binária",
        peso=1.0,
        tipo=TipoPergunta.BINARIA,
    )


@pytest.fixture
def pergunta_multipla() -> Pergunta:
    return Pergunta(
        codigo="Q-M",
        dimensao=Dimensao.FISCAL,
        texto="Múltipla",
        peso=1.0,
        tipo=TipoPergunta.MULTIPLA_ESCOLHA,
        multipla_total=4,
    )


@pytest.fixture
def pergunta_checklist() -> Pergunta:
    return Pergunta(
        codigo="Q-CL",
        dimensao=Dimensao.OPERACIONAL,
        texto="Checklist",
        peso=1.0,
        tipo=TipoPergunta.CHECKLIST,
        multipla_total=3,
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
        assert pergunta.aplicavel_para(empresa_padrao) is False
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
        assert pergunta.aplicavel_para(empresa_padrao) is False
        assert pergunta.aplicavel_para(empresa_lucro_real_industria) is True

    def test_pergunta_exclusiva_industria_e_lucro_real(self):
        empresa_industria_simples = EmpresaInfo(
            cnpj="12345678000195",
            razao_social="Indústria Simples",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
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

        assert pergunta.aplicavel_para(empresa_industria_simples) is False

    def test_setores_excluidos_bloqueia_mesmo_com_outras_condicoes_ok(
        self, empresa_lucro_real_industria
    ) -> None:
        """Setor listado em exclusão não responde à pergunta."""
        pergunta = Pergunta(
            codigo="Q-EXC",
            dimensao=Dimensao.OPERACIONAL,
            texto="Excluída para indústria",
            peso=1.0,
            tipo=TipoPergunta.BINARIA,
            condicao=CondicaoExibicao(
                regimes_permitidos=(RegimeTributario.LUCRO_REAL,),
                setores_excluidos=(SetorMacro.INDUSTRIA,),
            ),
        )
        assert pergunta.aplicavel_para(empresa_lucro_real_industria) is False

    def test_portes_permitidos_restringe_me_epp(self, empresa_padrao) -> None:
        """Porte fora da tupla ⇒ não aplicável."""
        pergunta_me_epp = Pergunta(
            codigo="Q-PORTE",
            dimensao=Dimensao.FISCAL,
            texto="Só ME/EPP",
            peso=1.0,
            tipo=TipoPergunta.TERNARIA,
            condicao=CondicaoExibicao(
                portes_permitidos=(PorteEmpresa.MEDIO, PorteEmpresa.GRANDE),
            ),
        )
        assert pergunta_me_epp.aplicavel_para(empresa_padrao) is False


class TestResposta:
    @pytest.mark.parametrize(
        "valor_bruto, pontuacao_esperada",
        [("sim", 100.0), ("SIM", 100.0), ("parcialmente", 50.0), ("nao", 0.0), ("NAO", 0.0)],
    )
    def test_calculo_pontuacao_ternaria_valida(
        self, valor_bruto, pontuacao_esperada, pergunta_ternaria
    ):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto=valor_bruto,
        )
        assert resposta.calcular_pontuacao(pergunta_ternaria) == pontuacao_esperada

    def test_calculo_pontuacao_ternaria_nao_se_aplica_exclui_media(self, pergunta_ternaria):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto="nao_se_aplica",
        )
        assert resposta.calcular_pontuacao(pergunta_ternaria) is None

    def test_calculo_pontuacao_ternaria_nao_comercializo_exclui_media(
        self, pergunta_ternaria
    ) -> None:
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto="nao_comercializo",
        )
        assert resposta.calcular_pontuacao(pergunta_ternaria) is None

    def test_calculo_pontuacao_ternaria_invalida(self, pergunta_ternaria):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.TERNARIA,
            valor_bruto="talvez",
        )
        with pytest.raises(ValueError, match=r"Valor inválido para pergunta ternária"):
            resposta.calcular_pontuacao(pergunta_ternaria)

    @pytest.mark.parametrize(
        "valor_bruto, pontuacao_esperada",
        [(1, 0.0), ("1", 0.0), (2, 25.0), (3, 50.0), (4, 75.0), (5, 100.0), ("5", 100.0)],
    )
    def test_calculo_pontuacao_escala_valida(
        self, valor_bruto, pontuacao_esperada, pergunta_escala
    ):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto=valor_bruto,
        )
        assert resposta.calcular_pontuacao(pergunta_escala) == pontuacao_esperada

    @pytest.mark.parametrize("valor_invalido", [0, 6, "6", -1])
    def test_calculo_pontuacao_escala_fora_limite(self, valor_invalido, pergunta_escala):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto=valor_invalido,
        )
        with pytest.raises(ValueError, match=r"Valor fora do limite da escala"):
            resposta.calcular_pontuacao(pergunta_escala)

    def test_calculo_pontuacao_escala_tipo_errado(self, pergunta_escala):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.ESCALA_1_5,
            valor_bruto="abc",
        )
        with pytest.raises(ValueError, match=r"Valor inválido para escala. Deve ser um número"):
            resposta.calcular_pontuacao(pergunta_escala)

    @pytest.mark.parametrize(
        "valor, esperado",
        [("sim", 100.0), ("nao", 0.0), ("1", 100.0), ("0", 0.0)],
    )
    def test_calculo_pontuacao_binaria(self, valor, esperado, pergunta_binaria):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.BINARIA,
            valor_bruto=valor,
        )
        assert resposta.calcular_pontuacao(pergunta_binaria) == esperado

    def test_calculo_pontuacao_binaria_valor_invalido(self, pergunta_binaria) -> None:
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.BINARIA,
            valor_bruto="talvez",
        )
        with pytest.raises(ValueError, match=r"Valor inválido para binária"):
            resposta.calcular_pontuacao(pergunta_binaria)

    def test_calculo_pontuacao_multipla(self, pergunta_multipla):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto='["a","b"]',
        )
        assert resposta.calcular_pontuacao(pergunta_multipla) == 50.0

    def test_calculo_pontuacao_multipla_lista_vazia_zero_pontos(self, pergunta_multipla):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto="[]",
        )
        assert resposta.calcular_pontuacao(pergunta_multipla) == 0.0

    def test_calculo_pontuacao_multipla_string_csv(self, pergunta_multipla):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto="x, y",
        )
        assert resposta.calcular_pontuacao(pergunta_multipla) == 50.0

    def test_calculo_pontuacao_multipla_lista_python(self, pergunta_multipla) -> None:
        """Valor já como lista (caso típico pós-parse JSON na API)."""
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto=["a", "b"],
        )
        assert resposta.calcular_pontuacao(pergunta_multipla) == 50.0

    def test_calculo_pontuacao_multipla_exige_multipla_total(self, pergunta_multipla):
        p_sem_total = Pergunta(
            codigo="Q-M2",
            dimensao=Dimensao.FISCAL,
            texto="Múltipla sem total",
            peso=1.0,
            tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            multipla_total=None,
        )
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto=["a"],
        )
        with pytest.raises(ValueError, match=r"multipla_total"):
            resposta.calcular_pontuacao(p_sem_total)

    def test_calculo_pontuacao_multipla_rejeita_mais_itens_que_total(self, pergunta_multipla):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto='["a","b","c","d","e"]',
        )
        with pytest.raises(ValueError, match=r"Mais itens selecionados"):
            resposta.calcular_pontuacao(pergunta_multipla)

    def test_calculo_pontuacao_checklist_mesma_logica_multipla(self, pergunta_checklist):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.CHECKLIST,
            valor_bruto=["opt_1", "opt_2"],
        )
        assert resposta.calcular_pontuacao(pergunta_checklist) == pytest.approx(200.0 / 3.0)

    def test_extrair_lista_json_invalido_nao_lista(self, pergunta_multipla):
        resposta = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.MULTIPLA_ESCOLHA,
            valor_bruto='{"x":1}',
        )
        with pytest.raises(ValueError, match=r"lista"):
            resposta.calcular_pontuacao(pergunta_multipla)

    def test_calculo_pontuacao_numerica_limites(self) -> None:
        resposta_num = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.NUMERICA,
            valor_bruto=50,
        )
        p_num = Pergunta(
            codigo="Q-N",
            dimensao=Dimensao.FISCAL,
            texto="N",
            peso=1.0,
            tipo=TipoPergunta.NUMERICA,
        )
        assert resposta_num.calcular_pontuacao(p_num) == 50.0

        resposta_fora = Resposta(
            diagnostico_id=uuid.uuid4(),
            pergunta_id=uuid.uuid4(),
            pergunta_tipo=TipoPergunta.NUMERICA,
            valor_bruto=101,
        )
        with pytest.raises(ValueError, match=r"entre 0 e 100"):
            resposta_fora.calcular_pontuacao(p_num)
