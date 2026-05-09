"""Testes — ``ConsultarCnpjUseCase``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.services.cnpj_consulta_service import ConsultaCnpjMaterializada
from src.application.use_cases.consultar_cnpj import ComandoConsultarCnpj, ConsultarCnpjUseCase


@pytest.mark.asyncio
async def test_sem_aplicar_diagnostico() -> None:
    exp = datetime.now(UTC) + timedelta(hours=1)
    mat = ConsultaCnpjMaterializada(
        consulta_id=uuid4(),
        cnpj_14="33014556000196",
        payload_bruto={},
        payload_canonico={"cnpj": "33014556000196"},
        fonte="brasil_api",
        expira_cadastral_at=exp,
        expira_qualificacao_at=exp,
        expira_situacao_at=exp,
    )
    svc = MagicMock()
    svc.materializar_consulta = AsyncMock(return_value=mat)
    uc = ConsultarCnpjUseCase(
        service=svc,
        cnpj_repo=MagicMock(),
        diagnostico_repo=MagicMock(),
    )
    cmd = ComandoConsultarCnpj(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="x",
        force_refresh=False,
        aplicar_no_diagnostico_id=None,
        trace_id=None,
    )
    out, aplicado = await uc.executar_e_materializar(cmd)
    assert out.consulta_id == mat.consulta_id
    assert aplicado is False
