"""Testes unitários — mapeamento e merge CNPJ → EmpresaInfo (camada APPLICATION)."""

from __future__ import annotations

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
