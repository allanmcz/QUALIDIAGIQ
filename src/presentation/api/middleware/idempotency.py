"""
Middleware de idempotência para POST mutáveis.

Base normativa (operações previsíveis ao contribuinte):
    - LC 214/2025 — disciplina do sistema tributário nacional (previsibilidade)

Camada: Presentation
Analogia Winthor: equivale a impedir INSERT duplicado pela mesma chave única de negócio.

Persistência: quando `app.state.idempotency_engine` existe (SQLAlchemy), usa Postgres;
caso contrário, TTL em memória (`cachetools`).
"""

from __future__ import annotations

import asyncio
import hashlib
from typing import TYPE_CHECKING, Any, cast

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from src.infrastructure.config.settings import get_settings
from src.infrastructure.idempotency.cached_response import CorpoCacheadoIdempotencia
from src.presentation.api.jwt_tenant_extract import tenant_id_from_bearer_authorization

if TYPE_CHECKING:
    from cachetools import TTLCache
    from sqlalchemy.engine import Engine
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.types import ASGIApp

# Limite para não armazenar PDF/base64 acidentalmente no cache MVP
_MAX_BODY_BYTES = 512 * 1024
_MAX_KEY_LEN = 128


def _exige_idempotencia(request: Request) -> bool:
    """Somente criação de diagnóstico (POST). Login e demais rotas ficam de fora."""
    if request.method.upper() != "POST":
        return False
    path = request.url.path
    return path in (
        "/diagnosticos",
        "/diagnosticos/",
        "/diagnosticos/self-service",
        "/diagnosticos/rascunho-self-service",
        "/diagnosticos/rascunho-self-service/concluir",
        "/diagnosticos/rascunho-self-service/vincular-conta",
        "/diagnosticos/vincular-leads-self-service",
        "/diagnosticos/vincular-leads-self-service/",
    )


def _chave_composta(request: Request, idempotency_key: str) -> str:
    """Isola cache por tenant implícito (Authorization) + chave + caminho."""
    auth = request.headers.get("authorization", "")
    material = f"{idempotency_key}|{request.url.path}|{request.method}|{auth}"
    return hashlib.sha256(material.encode()).hexdigest()


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Exige Idempotency-Key em POST /diagnosticos/ e replica respostas 2xx cacheadas."""

    def __init__(self, app: ASGIApp, cache: TTLCache[str, CorpoCacheadoIdempotencia]) -> None:
        super().__init__(app)
        self._cache = cache

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not _exige_idempotencia(request):
            return await call_next(request)

        raw_key = request.headers.get("Idempotency-Key") or request.headers.get("idempotency-key")
        if not raw_key or not str(raw_key).strip():
            return JSONResponse(
                status_code=400,
                content={
                    "detail": (
                        "Header Idempotency-Key obrigatório para POST sob /diagnosticos/ "
                        "(criação, self-service, rascunho self-service, concluir rascunho, vincular rascunho à conta, "
                        "vincular-leads-self-service)."
                    )
                },
            )

        idem_key = str(raw_key).strip()
        if len(idem_key) > _MAX_KEY_LEN:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Idempotency-Key deve ter no máximo {_MAX_KEY_LEN} caracteres"},
            )

        composta = _chave_composta(request, idem_key)
        engine = getattr(request.app.state, "idempotency_engine", None)
        ttl_sec = int(getattr(request.app.state, "idempotency_ttl_seconds", 3600))

        settings = get_settings()
        tenant_id = tenant_id_from_bearer_authorization(
            request.headers.get("authorization"),
            settings.jwt_secret_key.get_secret_value(),
            [settings.jwt_algorithm],
        )

        hit: CorpoCacheadoIdempotencia | None = None
        if engine is not None:
            from src.infrastructure.idempotency.postgres_backend import idempotency_get

            hit = await asyncio.to_thread(
                idempotency_get, cast("Engine", engine), composta, tenant_id
            )
        elif composta in self._cache:
            hit = self._cache[composta]

        if hit is not None:
            h = dict(hit.headers)
            h["X-Idempotent-Replay"] = "true"
            content_type = next(
                (v for k, v in hit.headers if k.lower() == "content-type"),
                None,
            )
            return Response(
                content=hit.body,
                status_code=hit.status_code,
                headers=h,
                media_type=content_type,
            )

        response = await call_next(request)

        body = b""
        iterator = getattr(response, "body_iterator", None)
        if iterator is not None:
            async for chunk in cast(Any, iterator):  # noqa: TC006
                body += chunk
        else:
            raw = getattr(response, "body", None)
            if raw is not None:
                body = raw if isinstance(raw, bytes) else bytes(raw)

        skip_headers = {"content-length", "transfer-encoding", "content-encoding"}
        passthrough: list[tuple[str, str]] = []
        for key, value in response.headers.items():
            if key.lower() not in skip_headers:
                passthrough.append((key, value))

        out = Response(
            content=body,
            status_code=response.status_code,
            headers=dict(passthrough),
            media_type=response.media_type,
        )

        if 200 <= response.status_code < 300 and len(body) <= _MAX_BODY_BYTES:
            cached = CorpoCacheadoIdempotencia(
                status_code=response.status_code,
                body=body,
                headers=tuple(passthrough),
            )
            if engine is not None:
                from src.infrastructure.idempotency.postgres_backend import idempotency_put

                await asyncio.to_thread(
                    idempotency_put,
                    cast("Engine", engine),
                    composta,
                    cached,
                    ttl_sec,
                    tenant_id,
                )
            elif composta not in self._cache:
                self._cache[composta] = cached

        return out
