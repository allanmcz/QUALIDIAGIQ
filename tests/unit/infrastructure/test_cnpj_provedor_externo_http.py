"""Testes — adapter HTTP CNPJ (BrasilAPI + fallback)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.adapters.cnpj_provedor_externo_http import CnpjProvedorExternoHttpAdapter


def _settings_mock() -> MagicMock:
    s = MagicMock()
    s.qdi_cnpj_brasil_api_base_url = "https://brasil.test/api/cnpj/v1"
    s.qdi_cnpj_minha_receita_url_template = "https://mr.test/{cnpj}"
    s.qdi_cnpj_http_timeout_seconds = 5.0
    return s


def _resp(status: int, payload: dict[str, object] | None = None) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.json.return_value = payload or {}
    return r


@pytest.mark.asyncio
async def test_brasil_api_200() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    ok = _resp(
        200,
        {
            "cnpj": "33014556000196",
            "razao_social": "ACME",
            "cnae_fiscal": 4711302,
            "uf": "RJ",
        },
    )
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=ok)

    with patch(
        "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
        return_value=mock_client,
    ):
        data, fonte, st, _ms = await adapter.buscar_cnpj("33014556000196")
    assert fonte == "brasil_api"
    assert st == 200
    assert data["razao_social"] == "ACME"


@pytest.mark.asyncio
async def test_brasil_404_sem_fallback() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=_resp(404))

    with (
        patch(
            "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
            return_value=mock_client,
        ),
        pytest.raises(ValueError, match="404"),
    ):
        await adapter.buscar_cnpj("33014556000196")


@pytest.mark.asyncio
async def test_fallback_minha_receita_quando_503() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    mr_payload = {
        "cnpj": "33014556000196",
        "razao_social": "ZETA",
        "cnae_fiscal": 4711302,
        "uf": "RJ",
    }
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(side_effect=[_resp(503), _resp(200, mr_payload)])

    with patch(
        "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
        return_value=mock_client,
    ):
        data, fonte, st, _ms = await adapter.buscar_cnpj("33014556000196")
    assert fonte == "minha_receita"
    assert st == 200
    assert data["razao_social"] == "ZETA"


@pytest.mark.asyncio
async def test_timeout_dispara_fallback() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    mr_payload = {"cnpj": "33014556000196", "razao_social": "Y", "cnae_fiscal": 4711302, "uf": "RJ"}
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(
        side_effect=[httpx.TimeoutException("timeout"), _resp(200, mr_payload)]
    )

    with patch(
        "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
        return_value=mock_client,
    ):
        _data, fonte, _st, _ms = await adapter.buscar_cnpj("33014556000196")
    assert fonte == "minha_receita"


@pytest.mark.asyncio
async def test_brasil_400_invalido() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=_resp(400))

    with (
        patch(
            "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
            return_value=mock_client,
        ),
        pytest.raises(ValueError, match="400"),
    ):
        await adapter.buscar_cnpj("33014556000196")


@pytest.mark.asyncio
async def test_fallback_minha_receita_tambem_falha() -> None:
    adapter = CnpjProvedorExternoHttpAdapter(_settings_mock())
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(side_effect=[_resp(503), httpx.RequestError("mr down")])

    with (
        patch(
            "src.infrastructure.adapters.cnpj_provedor_externo_http.httpx.AsyncClient",
            return_value=mock_client,
        ),
        pytest.raises(RuntimeError, match="Indisponível"),
    ):
        await adapter.buscar_cnpj("33014556000196")
