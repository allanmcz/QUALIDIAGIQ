"""Cobertura das factories de retificação e export portável."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    GerarExportPortabilidadeDiagnostico,
)
from src.application.use_cases.listar_retificacoes_diagnostico import (
    ListarRetificacoesDiagnostico,
)
from src.application.use_cases.registrar_retificacao_diagnostico import (
    RegistrarRetificacaoDiagnostico,
)
from src.presentation.api.dependencies import (
    get_diagnostico_retificacao_port,
    get_gerar_export_portabilidade_diagnostico_use_case,
    get_listar_retificacoes_diagnostico_use_case,
    get_registrar_retificacao_diagnostico_use_case,
)


def test_get_diagnostico_retificacao_port_sem_sync_database_url() -> None:
    with patch("src.presentation.api.deps_repositories_core.get_settings") as gs:
        gs.return_value.sync_database_url = None
        with pytest.raises(HTTPException) as ei:
            get_diagnostico_retificacao_port()
        assert ei.value.status_code == 503


def test_get_registrar_retificacao_diagnostico_use_case_factory() -> None:
    uc = get_registrar_retificacao_diagnostico_use_case(
        repo=MagicMock(),
        ret=MagicMock(),
    )
    assert isinstance(uc, RegistrarRetificacaoDiagnostico)


def test_get_listar_retificacoes_diagnostico_use_case_factory() -> None:
    uc = get_listar_retificacoes_diagnostico_use_case(ret=MagicMock())
    assert isinstance(uc, ListarRetificacoesDiagnostico)


def test_get_gerar_export_portabilidade_diagnostico_use_case_factory() -> None:
    uc = get_gerar_export_portabilidade_diagnostico_use_case(
        repo=MagicMock(),
        lgpd=MagicMock(),
    )
    assert isinstance(uc, GerarExportPortabilidadeDiagnostico)


def test_get_diagnostico_retificacao_port_com_dsn_retorna_adapter() -> None:
    from src.infrastructure.adapters.postgres_diagnostico_retificacao_adapter import (
        PostgresDiagnosticoRetificacaoAdapter,
    )

    with patch("src.presentation.api.deps_repositories_core.get_settings") as gs:
        gs.return_value.sync_database_url = "postgresql://u:p@localhost/db"
        port = get_diagnostico_retificacao_port()
        assert isinstance(port, PostgresDiagnosticoRetificacaoAdapter)
