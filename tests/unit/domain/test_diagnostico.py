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
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


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

    def test_registrar_score_completo_define_hash_e_snapshot(
        self, empresa_fixture, respondente_fixture
    ):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        diag.finalizar(score_geral=70.0)
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=12.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=12.0),
            },
        )
        diag.registrar_score_completo_para_evidencia(sc)
        assert diag.score_completo_snapshot is sc
        assert diag.hash_evidencia is not None
        assert len(diag.hash_evidencia) == 64

    def test_registrar_evidencia_rejeita_se_nao_finalizado(
        self, empresa_fixture, respondente_fixture
    ):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=1.0, peso_total_aplicado=1.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=1.0, peso_total_aplicado=1.0),
            },
        )
        with pytest.raises(DiagnosticoNaoFinalizavelError):
            diag.registrar_score_completo_para_evidencia(sc)

    def test_finalizar_e_registrar_evidencia_em_ordem(self, empresa_fixture, respondente_fixture):
        """Fluxo único domínio: finalização + snapshot (plano execução 11 — R8)."""
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=72.0, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=72.0, peso_total_aplicado=10.0),
            },
        )
        diag.finalizar_e_registrar_evidencia(sc)
        assert diag.status == StatusDiagnostico.FINALIZADO
        assert diag.score_geral == 72.0
        assert diag.score_completo_snapshot is sc
        assert diag.hash_evidencia is not None

    def test_definir_m12_autoconf_dez_itens(self, empresa_fixture, respondente_fixture):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        diag.finalizar(score_geral=50.0)
        itens = [True, False] * 5
        diag.definir_checklist_m12_autoconf(itens)
        assert diag.checklist_m12_estado == itens

    def test_definir_m12_rejeita_tamanho_invalido(self, empresa_fixture, respondente_fixture):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        diag.finalizar(score_geral=50.0)
        with pytest.raises(ValueError, match=r"exatamente 10"):
            diag.definir_checklist_m12_autoconf([True] * 9)

    def test_definir_m12_rejeita_se_nao_finalizado(self, empresa_fixture, respondente_fixture):
        diag = Diagnostico(
            tenant_id=uuid.uuid4(), empresa=empresa_fixture, respondente=respondente_fixture
        )
        with pytest.raises(
            DiagnosticoNaoFinalizavelError,
            match=r"autoconf M12",
        ):
            diag.definir_checklist_m12_autoconf([False] * 10)
