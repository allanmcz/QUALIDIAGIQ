"""Testes unitários — mapeamento e merge CNPJ → EmpresaInfo (camada APPLICATION)."""

from __future__ import annotations

import pytest

from src.application.services.cnpj_consulta_mapeamento import (
    mesclar_empresa_com_sugestao_cnpj,
    sugestao_desde_payload_receita,
)
from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro


class TestSugestaoDesdePayloadReceita:
    """Mapper BrasilAPI / Minha Receita → canónico."""

    def test_campos_minimos(self) -> None:
        payload = {
            "cnpj": "33014556000196",
            "razao_social": "LOJAS AMERICANAS S.A.",
            "cnae_fiscal": 4711302,
            "uf": "RJ",
            "descricao_situacao_cadastral": "BAIXADA",
            "codigo_porte": 5,
            "porte": "DEMAIS",
            "nome_fantasia": "Americanas",
            "municipio": "Rio de Janeiro",
            "logradouro": "Rua X",
        }
        s = sugestao_desde_payload_receita(payload)
        assert s["cnpj"] == "33014556000196"
        assert s["cnae_principal"] == "4711302"
        assert s["uf"] == "RJ"
        assert s["porte"] == "medio"

    @staticmethod
    def _base() -> dict[str, object]:
        return {
            "cnpj": "33014556000196",
            "razao_social": "X",
            "uf": "SP",
            "descricao_situacao_cadastral": "ATIVA",
        }

    def test_cnae_digitos_inferiores_a_sete_padding(self) -> None:
        p = {**self._base(), "cnae_fiscal": "47113"}
        assert sugestao_desde_payload_receita(p)["cnae_principal"] == "0047113"

    def test_cnae_none_e_setor_macro(self) -> None:
        p = {**self._base(), "cnae_fiscal": None}
        s = sugestao_desde_payload_receita(p)
        assert s["cnae_principal"] is None
        assert s["setor_macro"] is None

    def test_cnae_rejeita_com_mais_de_sete_digitos(self) -> None:
        p = {**self._base(), "cnae_fiscal": "12345678"}
        assert sugestao_desde_payload_receita(p)["cnae_principal"] is None

    @pytest.mark.parametrize(
        ("cnae", "setor"),
        [
            ("0113000", "agro"),
            ("0512300", "industria"),
            ("4210200", "consumo"),
            ("4512900", "comercio"),
            ("9612500", "servicos"),
        ],
    )
    def test_inferencia_setor_macro_por_prefixo(self, cnae: str, setor: str) -> None:
        p = {**self._base(), "cnae_fiscal": cnae}
        assert sugestao_desde_payload_receita(p)["setor_macro"] == setor

    @pytest.mark.parametrize(
        ("codigo", "porte_txt", "esperado"),
        [
            (1, "", "micro"),
            (3, "", "pequeno"),
            ("5", "", "medio"),
            ("x", "MEI XYZ", "micro"),
            (None, "MICRO EMPREENDEDOR", "micro"),
            (None, "EPP exemplo", "pequeno"),
            (None, "MÉDIO PORTE", "medio"),
            (None, "GRANDE", "medio"),
            (999, None, None),
            ("oops", "", None),
        ],
    )
    def test_porte_codigo_ou_texto(
        self, codigo: object, porte_txt: str | None, esperado: str | None
    ) -> None:
        p = {**self._base(), "codigo_porte": codigo, "porte": porte_txt}
        out = sugestao_desde_payload_receita(p)["porte"]
        assert out == esperado

    @pytest.mark.parametrize(
        ("payload_extra", "regime_esperado"),
        [
            ({"opcao_pelo_mei": True}, "mei"),
            ({"opcao_pelo_simples": True}, "simples_nacional"),
            (
                {
                    "regime_tributario": [
                        {"ano": "2024", "forma_de_tributacao": "LUCRO PRESUMIDO"},
                    ]
                },
                "lucro_presumido",
            ),
            (
                {
                    "regime_tributario": [
                        {"ano": 2020, "forma_de_tributacao": "SIMPLES"},
                        {"ano": 2023, "forma_de_tributacao": "LUCRO REAL"},
                    ]
                },
                "lucro_real",
            ),
            (
                {
                    "regime_tributario": [
                        {"ano": "não-numérico", "forma_de_tributacao": "MEI"},
                    ]
                },
                "mei",
            ),
            (
                {
                    "regime_tributario": [
                        {"ano": "não-converte", "forma_de_tributacao": "LUCRO PRESUMIDO"},
                    ]
                },
                "lucro_presumido",
            ),
            (
                {"regime_tributario": [{"ano": 2025, "forma_de_tributacao": "SIMPLES NACIONAL"}]},
                "simples_nacional",
            ),
            (
                {"regime_tributario": [{"ano": 2025, "forma_de_tributacao": "LUCRO REAL"}]},
                "lucro_real",
            ),
        ],
    )
    def test_regime_via_flags_ou_lista(
        self, payload_extra: dict[str, object], regime_esperado: str
    ) -> None:
        p = {**self._base(), **payload_extra}
        assert sugestao_desde_payload_receita(p)["regime"] == regime_esperado

    def test_inferencia_setor_macro_cnae_fora_faixas_conhecidas_servicos(self) -> None:
        """Prefixo CNAE que não cai em agro/indústria/consumo/comércio ⇒ ``servicos``."""
        p = {**self._base(), "cnae_fiscal": "4812300"}
        assert sugestao_desde_payload_receita(p)["setor_macro"] == "servicos"

    def test_uf_curta_ou_invalida(self) -> None:
        p = {**self._base(), "uf": "S"}
        assert sugestao_desde_payload_receita(p)["uf"] is None
        p2 = {**self._base(), "uf": "  "}
        assert sugestao_desde_payload_receita(p2)["uf"] is None

    def test_strings_opcionais_vazias(self) -> None:
        p = {
            "cnpj": "",
            "razao_social": "  ",
            "nome_fantasia": "",
            "municipio": None,
            "logradouro": "  ",
        }
        s = sugestao_desde_payload_receita(p)
        assert s["razao_social"] is None
        assert s["nome_fantasia"] is None
        assert s["municipio"] is None
        assert s["logradouro"] is None


class TestMesclarEmpresaComSugestaoCnpj:
    """Merge preenche vazios e sobrescreve divergentes."""

    def test_preenche_razao_vazia(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="4711302",
            uf="RJ",
            setor_macro=SetorMacro.COMERCIO,
        )
        sug = {"razao_social": "LOJAS AMERICANAS S.A.", "cnae_principal": "4711302"}
        nova, hist = mesclar_empresa_com_sugestao_cnpj(emp, sug, cnpj_consulta_14="33014556000196")
        assert nova.razao_social == "LOJAS AMERICANAS S.A."
        assert any(h[0] == "empresa_razao_social" for h in hist)

    def test_sobrescreve_cnae_diferente(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="6201500",
            uf="RJ",
            setor_macro=SetorMacro.SERVICOS,
        )
        sug = {"cnae_principal": "4711302"}
        nova, hist = mesclar_empresa_com_sugestao_cnpj(emp, sug, cnpj_consulta_14="33014556000196")
        assert nova.cnae_principal == "4711302"
        assert ("empresa_cnae", "6201500", "4711302") in hist

    def test_preenche_cnpj_quando_empresa_sem_cadastro_pj(self) -> None:
        emp = EmpresaInfo(
            cnpj="",
            razao_social="Lead",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="RJ",
            setor_macro=SetorMacro.COMERCIO,
        )
        sug: dict[str, object] = {}
        nova, hist = mesclar_empresa_com_sugestao_cnpj(emp, sug, cnpj_consulta_14="33014556000196")
        assert nova.cnpj == "33014556000196"
        assert ("empresa_cnpj", None, "33014556000196") in hist

    def test_sem_historico_razao_quando_equivalente_casefold(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="ACME Participacoes",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        sug = {"razao_social": "  acme   participacoes  "}
        _, hist = mesclar_empresa_com_sugestao_cnpj(emp, sug, cnpj_consulta_14="33014556000196")
        assert not any(h[0] == "empresa_razao_social" for h in hist)

    def test_ignora_porte_string_fora_do_enum(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        nova, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"porte": "nano"}, cnpj_consulta_14="33014556000196"
        )
        assert nova.porte == PorteEmpresa.MICRO
        assert not any(h[0] == "empresa_porte" for h in hist)

    def test_atualiza_regime_e_setor_quando_validos(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        sug = {"regime": "lucro_real", "setor_macro": "servicos"}
        nova, hist = mesclar_empresa_com_sugestao_cnpj(emp, sug, cnpj_consulta_14="33014556000196")
        assert nova.regime == RegimeTributario.LUCRO_REAL
        assert nova.setor_macro == SetorMacro.SERVICOS
        assert ("empresa_regime", "mei", "lucro_real") in hist
        assert ("empresa_setor_macro", "comercio", "servicos") in hist

    def test_sobrescreve_uf_quando_diferente(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        nova, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"uf": "RJ"}, cnpj_consulta_14="33014556000196"
        )
        assert nova.uf == "RJ"
        assert ("empresa_uf", "SP", "RJ") in hist

    def test_sobrescreve_porte_quando_valido_e_diferente(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        nova, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"porte": "medio"}, cnpj_consulta_14="33014556000196"
        )
        assert nova.porte == PorteEmpresa.MEDIO
        assert ("empresa_porte", "micro", "medio") in hist

    def test_preenche_uf_quando_empresa_sem_uf(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="4711302",
            uf="  ",
            setor_macro=SetorMacro.COMERCIO,
        )
        nova, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"uf": "RJ"}, cnpj_consulta_14="33014556000196"
        )
        assert nova.uf == "RJ"
        assert ("empresa_uf", None, "RJ") in hist

    def test_preenche_cnae_quando_vazio(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.MEI,
            cnae_principal="       ",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        nova, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"cnae_principal": "4711302"}, cnpj_consulta_14="33014556000196"
        )
        assert nova.cnae_principal == "4711302"
        assert ("empresa_cnae", None, "4711302") in hist

    def test_regime_igual_nao_gera_historico(self) -> None:
        emp = EmpresaInfo(
            cnpj="33014556000196",
            razao_social="X",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="4711302",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        _, hist = mesclar_empresa_com_sugestao_cnpj(
            emp, {"regime": "simples_nacional"}, cnpj_consulta_14="33014556000196"
        )
        assert not any(h[0] == "empresa_regime" for h in hist)
