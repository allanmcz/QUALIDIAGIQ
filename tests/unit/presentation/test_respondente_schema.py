"""Validação HTTP do respondente (nome obrigatório)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas import (
    EmpresaPainelSchema,
    EmpresaSchema,
    IniciarDiagnosticoPainelRequest,
    IniciarDiagnosticoRequest,
    RespondenteSchema,
)


def _empresa_min() -> dict:
    return {
        "cnpj": "12345678000195",
        "razao_social": "Empresa X",
        "porte": "micro",
        "regime": "simples_nacional",
        "cnae_principal": "1234567",
        "uf": "SP",
        "setor_macro": "comercio",
    }


class TestIniciarDiagnosticoAceitePrivacidade:
    """Checkbox LGPD obrigatório conforme wizard."""

    def test_rejeita_aceite_termos_false(self) -> None:
        with pytest.raises(ValidationError, match="privacidade"):
            IniciarDiagnosticoRequest.model_validate(
                {
                    "empresa": _empresa_min(),
                    "respondente": {"email": "a@b.com", "nome": "Maria"},
                    "respostas": [
                        {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}
                    ],
                    "aceite_termos_privacidade": False,
                }
            )


class TestRespondenteSchemaNomeObrigatorio:
    """POST /diagnosticos exige nome não vazio após strip."""

    def test_rejeita_sem_campo_nome(self) -> None:
        with pytest.raises(ValidationError) as ex:
            IniciarDiagnosticoRequest.model_validate(
                {
                    "empresa": _empresa_min(),
                    "respondente": {"email": "a@b.com"},
                    "respostas": [
                        {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}
                    ],
                    "aceite_termos_privacidade": True,
                }
            )
        assert "nome" in str(ex.value).lower()

    def test_rejeita_nome_somente_espacos(self) -> None:
        with pytest.raises(ValidationError):
            IniciarDiagnosticoRequest.model_validate(
                {
                    "empresa": _empresa_min(),
                    "respondente": {"email": "a@b.com", "nome": "   "},
                    "respostas": [
                        {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}
                    ],
                    "aceite_termos_privacidade": True,
                }
            )

    def test_aceita_nome_valido(self) -> None:
        body = IniciarDiagnosticoRequest.model_validate(
            {
                "empresa": _empresa_min(),
                "respondente": {"email": "a@b.com", "nome": "Maria"},
                "respostas": [{"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}],
                "aceite_termos_privacidade": True,
            }
        )
        assert body.respondente.nome == "Maria"


class TestRespondenteTelefoneBr:
    """Validador opcional BR (10/11 dígitos após limpeza)."""

    def test_telefone_none_e_vazio_opcional(self) -> None:
        r = RespondenteSchema(email="z@z.com", nome="N", telefone=None)
        assert r.telefone is None
        r2 = RespondenteSchema.model_validate({"email": "z@z.com", "nome": "N", "telefone": ""})
        assert r2.telefone is None
        r3 = RespondenteSchema.model_validate(
            {"email": "z@z.com", "nome": "N", "telefone": " ()- "}
        )
        assert r3.telefone is None

    def test_normaliza_fixo_dez_digitos(self) -> None:
        r = RespondenteSchema.model_validate(
            {"email": "z@z.com", "nome": "N", "telefone": "(11) 3456-7890"}
        )
        assert r.telefone == "1134567890"

    def test_normaliza_celular_onze_digitos(self) -> None:
        r = RespondenteSchema.model_validate(
            {"email": "z@z.com", "nome": "N", "telefone": "11987654321"}
        )
        assert r.telefone == "11987654321"

    def test_rejeita_digitos_forado_faixa_tipica(self) -> None:
        with pytest.raises(ValidationError, match="10 ou 11"):
            RespondenteSchema.model_validate(
                {"email": "z@z.com", "nome": "N", "telefone": "123456789"}
            )


class TestEmpresaSchemaCnpjOpcional:
    """Self-service / lead: CNPJ opcional; se informado, DV válido (ADR-013)."""

    def test_aceita_cnpj_vazio(self) -> None:
        d = _empresa_min()
        d["cnpj"] = ""
        e = EmpresaSchema.model_validate(d)
        assert e.cnpj == ""

    def test_aceita_cnpj_mascarado_valido(self) -> None:
        d = _empresa_min()
        d["cnpj"] = "12.345.678/0001-95"
        e = EmpresaSchema.model_validate(d)
        assert e.cnpj == "12345678000195"

    def test_aceita_omissao_chave_cnpj_como_vazio(self) -> None:
        d = {k: v for k, v in _empresa_min().items() if k != "cnpj"}
        e = EmpresaSchema.model_validate(d)
        assert e.cnpj == ""

    def test_rejeita_cnpj_parcial_quando_informado(self) -> None:
        d = _empresa_min()
        d["cnpj"] = "1234567800019"
        with pytest.raises(ValidationError):
            EmpresaSchema.model_validate(d)

    def test_rejeita_cnpj_todos_digitos_iguais(self) -> None:
        d = _empresa_min()
        d["cnpj"] = "11.111.111/1111-11"
        with pytest.raises(ValidationError, match="iguais"):
            EmpresaSchema.model_validate(d)

    def test_rejeita_cnpj_quatorze_digitos_com_dv_invalido(self) -> None:
        d = _empresa_min()
        d["cnpj"] = "12345678000190"
        with pytest.raises(ValidationError, match="verificadores"):
            EmpresaSchema.model_validate(d)

    def test_rejeita_uf_fora_catalogo_ibge(self) -> None:
        d = _empresa_min()
        d["uf"] = "ZX"
        with pytest.raises(ValidationError, match="UF"):
            EmpresaSchema.model_validate(d)


class TestEmpresaPainelSchemaCnpjObrigatorio:
    """Painel / vinculação: CNPJ obrigatório (ADR-013)."""

    def test_rejeita_cnpj_vazio(self) -> None:
        d = dict(_empresa_min())
        d["cnpj"] = ""
        with pytest.raises(ValidationError, match=r"(obrigatório|CNPJ)"):
            EmpresaPainelSchema.model_validate(d)

    def test_aceita_cnpj_valido(self) -> None:
        e = EmpresaPainelSchema.model_validate(_empresa_min())
        assert e.cnpj == "12345678000195"

    def test_iniciar_diagnostico_painel_rejeita_sem_cnpj(self) -> None:
        with pytest.raises(ValidationError):
            IniciarDiagnosticoPainelRequest.model_validate(
                {
                    "empresa": {
                        "cnpj": "",
                        "razao_social": "Empresa",
                        "porte": "micro",
                        "regime": "simples_nacional",
                        "cnae_principal": "1234567",
                        "uf": "SP",
                        "setor_macro": "comercio",
                    },
                    "respondente": {"email": "a@b.com", "nome": "Maria"},
                    "respostas": [
                        {"pergunta_id": "1f74e164-195d-5fde-ba27-8ae08b8e011e", "valor": 4}
                    ],
                    "aceite_termos_privacidade": True,
                }
            )
