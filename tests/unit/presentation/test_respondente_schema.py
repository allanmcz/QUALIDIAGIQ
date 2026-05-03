"""Validação HTTP do respondente (nome obrigatório)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas import EmpresaSchema, IniciarDiagnosticoRequest


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


class TestEmpresaSchemaCnpjOpcional:
    """POST /diagnosticos: CNPJ opcional; se informado, DV válido (regra produto QDI)."""

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
