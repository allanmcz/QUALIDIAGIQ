"""Testes — erro 400 no GET ``/diagnosticos/questionario`` quando use case levanta ``ValueError``."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.presentation.api.dependencies import get_gerar_questionario_adaptativo_use_case
from src.presentation.api.main import app

client = TestClient(app)

_URL_BASE = (
    "/diagnosticos/questionario"
    "?cnpj=&razao_social=Acme+Teste"
    "&porte=micro&regime=simples_nacional&cnae_principal=1234567&uf=SP&setor_macro=comercio"
)


def test_questionario_adaptativo_value_error_400() -> None:
    mock_uc = MagicMock()
    mock_uc.execute.side_effect = ValueError("Motor adaptativo: inconsistente para teste.")

    app.dependency_overrides[get_gerar_questionario_adaptativo_use_case] = lambda: mock_uc
    try:
        res = client.get(_URL_BASE)
        assert res.status_code == 400
        assert "inconsistente" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_gerar_questionario_adaptativo_use_case, None)
