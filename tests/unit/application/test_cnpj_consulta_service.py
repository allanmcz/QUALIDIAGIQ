"""Testes — ``CnpjConsultaService`` (cache, idempotência, chamada externa)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.services.cnpj_consulta_service import CnpjConsultaService, CnpjTtlSegundos


def _row_base() -> dict[str, object]:
    cid = uuid4()
    exp = datetime.now(UTC) + timedelta(days=1)
    return {
        "id": cid,
        "cnpj": "33014556000196",
        "payload_bruto": {"k": 1},
        "payload_canonico": {
            "cnpj": "33014556000196",
            "razao_social": "ACME",
            "cnae_principal": "4711302",
            "uf": "RJ",
        },
        "fonte": "brasil_api",
        "expira_cadastral_at": exp,
        "expira_qualificacao_at": exp,
        "expira_situacao_at": exp,
    }


@pytest.mark.asyncio
async def test_reusa_linha_idempotente_sem_http() -> None:
    row = _row_base()
    repo = MagicMock()
    repo.buscar_por_idempotencia.return_value = row
    provedor = AsyncMock()
    svc = CnpjConsultaService(repo, provedor, CnpjTtlSegundos(3600, 3600, 3600))
    out = await svc.materializar_consulta(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="idem-1",
        force_refresh=False,
        diagnostico_id=None,
        trace_id=None,
    )
    assert out.consulta_id == row["id"]
    provedor.buscar_cnpj.assert_not_called()
    repo.buscar_ultimo_cache_valido_triplo_ttl.assert_not_called()


@pytest.mark.asyncio
async def test_cache_ttl_insere_nova_linha_sem_http() -> None:
    row = _row_base()
    repo = MagicMock()
    repo.buscar_por_idempotencia.return_value = None
    repo.buscar_ultimo_cache_valido_triplo_ttl.return_value = row
    novo_id = uuid4()
    repo.inserir_consulta.return_value = novo_id
    provedor = AsyncMock()
    svc = CnpjConsultaService(repo, provedor, CnpjTtlSegundos(60, 120, 180))
    out = await svc.materializar_consulta(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="idem-2",
        force_refresh=False,
        diagnostico_id=None,
        trace_id="t1",
    )
    assert out.consulta_id == novo_id
    provedor.buscar_cnpj.assert_not_called()
    repo.inserir_consulta.assert_called_once()


@pytest.mark.asyncio
async def test_force_refresh_chama_provedor() -> None:
    repo = MagicMock()
    repo.buscar_por_idempotencia.return_value = None
    repo.buscar_ultimo_cache_valido_triplo_ttl.return_value = _row_base()
    novo_id = uuid4()
    repo.inserir_consulta.return_value = novo_id
    provedor = MagicMock()
    provedor.buscar_cnpj = AsyncMock(
        return_value=(
            {
                "cnpj": "33014556000196",
                "razao_social": "OUTRA",
                "cnae_fiscal": 4711302,
                "uf": "RJ",
            },
            "brasil_api",
            200,
            42,
        )
    )
    svc = CnpjConsultaService(repo, provedor, CnpjTtlSegundos(86400, 3600, 900))
    out = await svc.materializar_consulta(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="idem-3",
        force_refresh=True,
        diagnostico_id=None,
        trace_id=None,
    )
    assert out.consulta_id == novo_id
    provedor.buscar_cnpj.assert_awaited_once()
    repo.buscar_ultimo_cache_valido_triplo_ttl.assert_not_called()
