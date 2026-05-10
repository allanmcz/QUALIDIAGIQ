"""Testes HTTP — ``GET /referencia/cnae/subclasses`` com use case mockado."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo
from src.presentation.api.dependencies import get_buscar_cnae_subclasses_use_case
from src.presentation.api.main import app

client = TestClient(app)


def test_cnae_subclasses_200_com_itens() -> None:
    linha = CnaeSubclasseResumo(subclasse_id="4712100", descricao="Comércio varejista")
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(return_value=[linha])

    app.dependency_overrides[get_buscar_cnae_subclasses_use_case] = lambda: mock_uc
    try:
        res = client.get("/referencia/cnae/subclasses?q=47&limite=10")
        assert res.status_code == 200
        body = res.json()
        assert len(body["itens"]) == 1
        assert body["itens"][0]["subclasse_id"] == "4712100"
        assert "varejista" in body["itens"][0]["descricao"]
        mock_uc.execute.assert_awaited_once_with(consulta="47", limite=10)
    finally:
        app.dependency_overrides.pop(get_buscar_cnae_subclasses_use_case, None)


def test_cnae_subclasses_value_error_400() -> None:
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(side_effect=ValueError("Parâmetro reprovado na aplicação"))

    app.dependency_overrides[get_buscar_cnae_subclasses_use_case] = lambda: mock_uc
    try:
        res = client.get("/referencia/cnae/subclasses?q=ab&limite=5")
        assert res.status_code == 400
        assert "reprovado" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_buscar_cnae_subclasses_use_case, None)


def test_cnae_subclasses_runtime_error_503() -> None:
    mock_uc = MagicMock()
    mock_uc.execute = AsyncMock(side_effect=RuntimeError("DATABASE_URL indisponível"))

    app.dependency_overrides[get_buscar_cnae_subclasses_use_case] = lambda: mock_uc
    try:
        res = client.get("/referencia/cnae/subclasses?q=ab")
        assert res.status_code == 503
        assert "DATABASE_URL" in res.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_buscar_cnae_subclasses_use_case, None)
