"""
Adapter HTTP — BrasilAPI com fallback Minha Receita só em falha de rede/timeout/5xx.

Camada: Infrastructure
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog

from src.application.ports.cnpj_provedor_externo_port import CnpjProvedorExternoPort
from src.infrastructure.config.settings import Settings
from src.infrastructure.observability.qdi_otel_metrics import record_cnpj_lookup

logger = structlog.get_logger(__name__)


class CnpjProvedorExternoHttpAdapter(CnpjProvedorExternoPort):
    """Cliente async httpx — não chama fallback em HTTP 404 da BrasilAPI."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def buscar_cnpj(self, cnpj_14: str) -> tuple[dict[str, Any], str, int, int]:
        base = self._settings.qdi_cnpj_brasil_api_base_url.rstrip("/")
        url_br = f"{base}/{cnpj_14}"
        timeout = httpx.Timeout(self._settings.qdi_cnpj_http_timeout_seconds)

        t0 = time.perf_counter()

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(url_br)
            except httpx.TimeoutException as e:
                logger.warning(
                    "cnpj_brasil_api_timeout",
                    cnpj_radical=cnpj_14[:8],
                    erro=str(e),
                )
                record_cnpj_lookup(fonte="brasil_api", http_status_group="timeout")
                return await self._fallback_minha_receita(client, cnpj_14, t0)
            except httpx.RequestError as e:
                logger.warning(
                    "cnpj_brasil_api_rede",
                    cnpj_radical=cnpj_14[:8],
                    erro=str(e),
                )
                record_cnpj_lookup(fonte="brasil_api", http_status_group="rede")
                return await self._fallback_minha_receita(client, cnpj_14, t0)

            ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code == 404:
                record_cnpj_lookup(fonte="brasil_api", http_status_group="4xx")
                raise ValueError(
                    "CNPJ não encontrado na consulta BrasilAPI (equivalente 404 Receita)."
                )
            if resp.status_code >= 500:
                logger.warning(
                    "cnpj_brasil_api_fallback",
                    cnpj_radical=cnpj_14[:8],
                    status=resp.status_code,
                )
                record_cnpj_lookup(fonte="brasil_api", http_status_group="5xx")
                return await self._fallback_minha_receita(client, cnpj_14, t0)
            if resp.status_code == 429:
                logger.warning(
                    "cnpj_brasil_api_fallback",
                    cnpj_radical=cnpj_14[:8],
                    status=resp.status_code,
                )
                record_cnpj_lookup(fonte="brasil_api", http_status_group="4xx")
                return await self._fallback_minha_receita(client, cnpj_14, t0)

            if resp.status_code >= 400:
                record_cnpj_lookup(fonte="brasil_api", http_status_group="4xx")
                raise ValueError(f"BrasilAPI retornou status {resp.status_code}.")

            try:
                data = resp.json()
            except ValueError as e:
                record_cnpj_lookup(fonte="brasil_api", http_status_group="unknown")
                raise ValueError("Resposta BrasilAPI não é JSON válido.") from e
            if not isinstance(data, dict):
                record_cnpj_lookup(fonte="brasil_api", http_status_group="unknown")
                raise ValueError("Payload BrasilAPI inválido.")
            record_cnpj_lookup(fonte="brasil_api", http_status_group="2xx")
            return data, "brasil_api", resp.status_code, ms

    async def _fallback_minha_receita(
        self,
        client: httpx.AsyncClient,
        cnpj_14: str,
        t0: float,
    ) -> tuple[dict[str, Any], str, int, int]:
        tpl = self._settings.qdi_cnpj_minha_receita_url_template
        url_mr = tpl.format(cnpj=cnpj_14)
        try:
            resp = await client.get(url_mr)
        except httpx.TimeoutException as e:
            logger.error(
                "cnpj_minha_receita_falhou",
                cnpj_radical=cnpj_14[:8],
                erro=str(e),
            )
            record_cnpj_lookup(fonte="minha_receita", http_status_group="timeout")
            raise RuntimeError(
                "Indisponível consultar CNPJ nas fontes públicas (BrasilAPI e Minha Receita)."
            ) from e
        except httpx.RequestError as e:
            logger.error(
                "cnpj_minha_receita_falhou",
                cnpj_radical=cnpj_14[:8],
                erro=str(e),
            )
            record_cnpj_lookup(fonte="minha_receita", http_status_group="rede")
            raise RuntimeError(
                "Indisponível consultar CNPJ nas fontes públicas (BrasilAPI e Minha Receita)."
            ) from e

        ms = int((time.perf_counter() - t0) * 1000)
        if resp.status_code >= 400:
            if resp.status_code >= 500:
                record_cnpj_lookup(fonte="minha_receita", http_status_group="5xx")
            else:
                record_cnpj_lookup(fonte="minha_receita", http_status_group="4xx")
            raise RuntimeError(f"Fallback Minha Receita falhou com HTTP {resp.status_code}.")
        try:
            data = resp.json()
        except ValueError as e:
            record_cnpj_lookup(fonte="minha_receita", http_status_group="unknown")
            raise RuntimeError("Fallback Minha Receita não retornou JSON válido.") from e
        if not isinstance(data, dict):
            record_cnpj_lookup(fonte="minha_receita", http_status_group="unknown")
            raise RuntimeError("Payload Minha Receita inválido.")
        record_cnpj_lookup(fonte="minha_receita", http_status_group="2xx")
        return data, "minha_receita", resp.status_code, ms
