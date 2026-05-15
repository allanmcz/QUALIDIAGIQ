"""Cobre registro de uso LLM após POST explicacao-score-llm (linha com DSN)."""

from __future__ import annotations

import copy
import uuid
from unittest.mock import AsyncMock, patch

from src.domain.ports.llm_gateway import LlmGatewayResponse
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_diagnostico_repository,
    get_explicar_score_llm_use_case,
)
from src.presentation.api.main import app
from tests.conftest import cabecalho_post_diagnostico
from tests.unit.presentation.test_api import (
    _diag_finalizado_micro,
    _score_completo_snapshot_http,
    client,
)


def test_post_explicacao_score_llm_registra_uso_quando_dsn() -> None:
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    d_snap = copy.deepcopy(_diag_finalizado_micro())
    d_snap.tenant_id = tid
    d_snap.score_completo_snapshot = _score_completo_snapshot_http(62.0, 40.0)

    mock_uc = AsyncMock()
    mock_uc.execute = AsyncMock(
        return_value=LlmGatewayResponse(
            text="ok",
            provider="fake",
            model="m",
            policy_version="v",
        )
    )
    mock_repo = AsyncMock()
    mock_repo.buscar_por_id = AsyncMock(return_value=d_snap)
    mock_repo.atualizar_explicacao_score_llm = AsyncMock()
    mock_repo.registrar_explicacao_score_llm_historico = AsyncMock()

    app.dependency_overrides[get_explicar_score_llm_use_case] = lambda: mock_uc
    app.dependency_overrides[get_diagnostico_repository] = lambda: mock_repo
    app.dependency_overrides[get_current_user_tenant] = lambda: (uid, tid, "avancado")

    with patch(
        "src.presentation.api.routers.diagnostico_painel_router.get_settings"
    ) as mock_settings:
        mock_settings.return_value.sync_database_url = "postgresql://local/db"
        mock_settings.return_value.llm_quota_explicacao_score_daily = 0
        with patch(
            "src.presentation.api.routers.diagnostico_painel_router.registrar_uso_llm_sync"
        ) as mock_reg:
            response = client.post(
                f"/diagnosticos/{d_snap.id}/explicacao-score-llm",
                headers=cabecalho_post_diagnostico(usuario_id=uid, tenant_id=tid),
            )
            mock_reg.assert_called_once()

    app.dependency_overrides.clear()
    assert response.status_code == 200
