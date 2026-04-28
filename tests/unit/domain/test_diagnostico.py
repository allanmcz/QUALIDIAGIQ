import uuid

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    DiagnosticoNaoFinalizavelError,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)


class TestEmpresaInfo:
    def test_deve_criar_empresa_valida(self):
        empresa = EmpresaInfo(
            cnpj="12345678000199",
            razao_social="Empresa Teste LTDA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.INDUSTRIA,
        )
        assert empresa.cnpj == "12345678000199"
        assert empresa.uf == "SP"

    @pytest.mark.parametrize("cnpj_invalido", ["1234567800019", "123456780001999"])
    def test_deve_rejeitar_cnpj_com_comprimento_invalido(self, cnpj_invalido):
        with pytest.raises(ValueError, match=r"CNPJ deve conter exatamente 14 dígitos numéricos"):
            EmpresaInfo(
                cnpj=cnpj_invalido,
                razao_social="Teste",
                porte=PorteEmpresa.MICRO,
                regime=RegimeTributario.SIMPLES_NACIONAL,
                cnae_principal="1234567",
                uf="RJ",
                setor_macro=SetorMacro.COMERCIO,
            )

    @pytest.mark.parametrize("cnpj_invalido", ["12.345.678/000", "ABC45678000199"])
    def test_deve_rejeitar_cnpj_nao_numerico(self, cnpj_invalido):
        with pytest.raises(ValueError, match=r"CNPJ deve conter exatamente 14 dígitos numéricos"):
            EmpresaInfo(
                cnpj=cnpj_invalido,
                razao_social="Teste",
                porte=PorteEmpresa.MICRO,
                regime=RegimeTributario.SIMPLES_NACIONAL,
                cnae_principal="1234567",
                uf="RJ",
                setor_macro=SetorMacro.COMERCIO,
            )

    @pytest.mark.parametrize("uf_invalida", ["S", "SPP"])
    def test_deve_rejeitar_uf_invalida(self, uf_invalida):
        with pytest.raises(ValueError, match=r"UF deve ter 2 caracteres"):
            EmpresaInfo(
                cnpj="12345678000199",
                razao_social="Teste",
                porte=PorteEmpresa.MICRO,
                regime=RegimeTributario.SIMPLES_NACIONAL,
                cnae_principal="1234567",
                uf=uf_invalida,
                setor_macro=SetorMacro.COMERCIO,
            )


class TestRespondente:
    def test_deve_criar_respondente_completo(self):
        resp = Respondente(email="teste@teste.com", nome="João", cargo="CFO")
        assert resp.email == "teste@teste.com"
        assert resp.nome == "João"
        assert resp.cargo == "CFO"

    def test_deve_criar_respondente_apenas_com_email(self):
        resp = Respondente(email="teste@teste.com")
        assert resp.email == "teste@teste.com"
        assert resp.nome is None
        assert resp.cargo is None


@pytest.fixture
def empresa_fixture():
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
def respondente_fixture():
    return Respondente(email="teste@teste.com")


class TestDiagnostico:
    def test_estado_inicial_deve_ser_em_andamento(self, empresa_fixture, respondente_fixture):
        tenant_id = uuid.uuid4()
        diag = Diagnostico(
            tenant_id=tenant_id, empresa=empresa_fixture, respondente=respondente_fixture
        )

        assert diag.tenant_id == tenant_id
        assert diag.status == StatusDiagnostico.EM_ANDAMENTO
        assert diag.score_geral is None
        assert diag.relatorio_pdf_url is None
        assert diag.finalizado_em is None

    def test_deve_finalizar_diagnostico_com_sucesso(self, empresa_fixture, respondente_fixture):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )

        diag.finalizar(score_geral=85.5)

        assert diag.status == StatusDiagnostico.FINALIZADO
        assert diag.score_geral == 85.5
        assert diag.finalizado_em is not None

    @pytest.mark.parametrize("score_invalido", [-1.0, 101.0])
    def test_deve_rejeitar_finalizacao_com_score_invalido(
        self, empresa_fixture, respondente_fixture, score_invalido
    ):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )

        with pytest.raises(ValueError, match=r"Score geral inválido:"):
            diag.finalizar(score_geral=score_invalido)

    def test_deve_rejeitar_finalizacao_de_diagnostico_nao_em_andamento(
        self, empresa_fixture, respondente_fixture
    ):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        diag.finalizar(score_geral=50.0)  # finaliza a primeira vez

        # tenta finalizar novamente
        with pytest.raises(
            DiagnosticoNaoFinalizavelError, match=r"não pode ser finalizado novamente"
        ):
            diag.finalizar(score_geral=60.0)

    def test_deve_anexar_relatorio_com_sucesso(self, empresa_fixture, respondente_fixture):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        diag.finalizar(score_geral=50.0)

        url = "https://supabase.com/storage/v1/object/public/reports/123.pdf"
        diag.anexar_relatorio(url)

        assert diag.relatorio_pdf_url == url

    def test_deve_rejeitar_anexar_relatorio_se_nao_finalizado(
        self, empresa_fixture, respondente_fixture
    ):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )

        url = "https://supabase.com/storage/v1/object/public/reports/123.pdf"
        with pytest.raises(
            DiagnosticoNaoFinalizavelError,
            match=r"Só é possível anexar relatório a um diagnóstico finalizado",
        ):
            diag.anexar_relatorio(url)
