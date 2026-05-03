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


class TestEmpresaSchemaCnpjObrigatorio:
    """POST /diagnosticos exige CNPJ válido (cadastro PJ no diagnóstico)."""

    def test_rejeita_cnpj_vazio(self) -> None:
        d = _empresa_min()
        d["cnpj"] = ""
        with pytest.raises(ValidationError) as ex:
            EmpresaSchema.model_validate(d)
        assert "obrigatório" in str(ex.value).lower() or "cnpj" in str(ex.value).lower()

    def test_aceita_cnpj_mascarado_valido(self) -> None:
        d = _empresa_min()
        d["cnpj"] = "12.345.678/0001-95"
        e = EmpresaSchema.model_validate(d)
        assert e.cnpj == "12345678000195"
