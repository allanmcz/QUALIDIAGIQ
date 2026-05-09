"""Testes — ``CnpjConsultaService`` (cache, idempotência, chamada externa)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.services.cnpj_consulta_service import (
    CnpjConsultaService,
    CnpjTtlSegundos,
    _expiries,
)


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
async def test_sem_linha_idempotente_nem_cache_ttl_chama_provedor() -> None:
    """``force_refresh=false`` + sem cache válido → fluxo normal na rede."""
    repo = MagicMock()
    repo.buscar_por_idempotencia.return_value = None
    repo.buscar_ultimo_cache_valido_triplo_ttl.return_value = None
    novo_id = uuid4()
    repo.inserir_consulta.return_value = novo_id
    provedor = MagicMock()
    provedor.buscar_cnpj = AsyncMock(
        return_value=(
            {
                "cnpj": "33014556000196",
                "razao_social": "ACME",
                "cnae_fiscal": 4711302,
                "uf": "RJ",
            },
            "brasil_api",
            200,
            15,
        ),
    )
    svc = CnpjConsultaService(repo, provedor, CnpjTtlSegundos(3600, 3600, 3600))
    out = await svc.materializar_consulta(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="idem-sem-cache",
        force_refresh=False,
        diagnostico_id=None,
        trace_id=None,
    )
    assert out.consulta_id == novo_id
    provedor.buscar_cnpj.assert_awaited_once()
    repo.buscar_ultimo_cache_valido_triplo_ttl.assert_called_once()


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


def test_expiries_datetime_naive_recebe_tz_utc() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    exp_c, _, _ = _expiries(CnpjTtlSegundos(60, 120, 180), naive)
    assert exp_c.tzinfo is UTC


def test_row_materializada_payload_bruto_nao_dict_vira_dict_vazio() -> None:
    row = _row_base()
    row["payload_bruto"] = None
    row["payload_canonico"] = ["não", "é", "dict"]
    repo = MagicMock()
    svc = CnpjConsultaService(repo, AsyncMock(), CnpjTtlSegundos(1, 1, 1))
    mat = svc._row_materializada(row)
    assert mat.payload_bruto == {}
    assert mat.payload_canonico == {}


@pytest.mark.asyncio
async def test_force_refresh_canon_sem_cnpj_corrigido_para_cnpj_14() -> None:
    repo = MagicMock()
    repo.buscar_por_idempotencia.return_value = None
    novo_id = uuid4()
    repo.inserir_consulta.return_value = novo_id
    provedor = MagicMock()
    provedor.buscar_cnpj = AsyncMock(
        return_value=(
            {
                "razao_social": "SEM CAMPO CNPJ NO JSON",
                "cnae_fiscal": 4711302,
                "uf": "RJ",
            },
            "brasil_api",
            200,
            10,
        )
    )
    svc = CnpjConsultaService(repo, provedor, CnpjTtlSegundos(3600, 3600, 3600))
    out = await svc.materializar_consulta(
        tenant_id=uuid4(),
        cnpj_14="33014556000196",
        idempotency_key="idem-sem-cnpj-no-json",
        force_refresh=True,
        diagnostico_id=None,
        trace_id=None,
    )
    assert out.cnpj_14 == "33014556000196"
    assert out.payload_canonico.get("cnpj") == "33014556000196"
    provedor.buscar_cnpj.assert_awaited_once()
