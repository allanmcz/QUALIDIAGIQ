"""Fixtures partilhados dos testes de presentation (HTTP)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.presentation.api.dependencies import get_diagnostico_repository
from src.presentation.api.main import app


@pytest.fixture(autouse=True)
def _mock_diagnostico_repository_get_http(request: pytest.FixtureRequest) -> None:
    """
    GET/POST de diagnóstico resolvem ``get_diagnostico_repository`` para ``_montar_diagnostico_response``.

    Evita instanciar Supabase real (``supabase_key is required``) quando o teste só mocka o use case.
    """
    if request.node.get_closest_marker("no_auto_diagnostico_repo"):
        yield
        return
    m = MagicMock()
    m.buscar_plano_painel_serializado = AsyncMock(
        return_value=PlanoPainelSerializado(
            versao_plano=1,
            checklist=(),
            matriz_impacto=(),
            cronograma=(),
        )
    )
    app.dependency_overrides[get_diagnostico_repository] = lambda: m
    yield
    app.dependency_overrides.pop(get_diagnostico_repository, None)
