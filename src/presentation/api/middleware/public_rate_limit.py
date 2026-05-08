"""
Rate limiting leve para rotas públicas (por IP e janela de 1 minuto).

Camada: Presentation
Endpoints: prefixos normativa + manifesto/metodologia/questionário + CNAE referência (GET/públicos).

Analogia: quota por sessão no Oracle — aqui em memória por processo (MVP).
"""

from __future__ import annotations

from threading import Lock
from time import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.infrastructure.config.settings import get_settings

if TYPE_CHECKING:
    from starlette.middleware.base import RequestResponseEndpoint
    from starlette.requests import Request
    from starlette.responses import Response

_lock = Lock()
_contagens: dict[tuple[str, int, str], int] = {}


def _bucket_minuto() -> int:
    return int(time() // 60)


def _grupo_rota_publica(path: str) -> str | None:
    if path.startswith("/normativa"):
        return "public_normativa"
    if path.startswith("/diagnosticos/questionario"):
        return "public_diag_catalogo"
    if path in ("/diagnosticos/manifesto-pesos", "/diagnosticos/metodologia"):
        return "public_diag_catalogo"
    if path.startswith("/referencia/cnae"):
        return "public_cnae"
    if path == "/public/institucional":
        return "public_institucional"
    return None


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    """429 quando o mesmo IP excede N requisições/minuto no grupo de rota."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.public_rate_limit_enabled:
            return await call_next(request)
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        grupo = _grupo_rota_publica(request.url.path)
        if grupo is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        chave = (ip, _bucket_minuto(), grupo)
        limite = settings.public_rate_limit_per_minute

        with _lock:
            atual = _contagens.get(chave, 0) + 1
            _contagens[chave] = atual
            if atual > limite:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Limite de requisições públicas excedido. Tente novamente em até 1 minuto."
                    },
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)
