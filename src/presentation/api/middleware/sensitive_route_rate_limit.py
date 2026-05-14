"""
Rate limit agressivo para rotas de autenticação e self-service (ADR-020).

Camada: Presentation
Objetivo: mitigar brute-force e abuso de OTP / rascunho sem afetar todo POST /diagnosticos/.

Analogia: fila separada com cota baixa só para «INSERT sensível» — distinto do catálogo público.
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


def _grupo_rota_sensivel(method: str, path: str) -> str | None:
    """Retorna chave de grupo ou None se a rota não estiver sujeita a este limite."""
    if method.upper() != "POST":
        return None
    if path == "/auth/login" or path.rstrip("/") == "/auth/login":
        return "sensivel_auth_login"
    if path == "/auth/cadastro" or path.rstrip("/") == "/auth/cadastro":
        return "sensivel_auth_cadastro"
    if path == "/auth/verificar-email/solicitar":
        return "sensivel_auth_otp_solicitar"
    if path == "/auth/verificar-email/confirmar":
        return "sensivel_auth_otp_confirmar"
    if path.startswith("/diagnosticos/rascunho-self-service"):
        return "sensivel_diag_rascunho_ss"
    return None


class SensitiveRouteRateLimitMiddleware(BaseHTTPMiddleware):
    """429 quando o mesmo IP excede N POST/minuto em rotas sensíveis (MVP ADR-020)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.sensitive_rate_limit_enabled:
            return await call_next(request)
        if request.method.upper() == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        grupo = _grupo_rota_sensivel(request.method, path)
        if grupo is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        chave = (ip, _bucket_minuto(), grupo)
        limite = settings.sensitive_rate_limit_per_minute

        with _lock:
            atual = _contagens.get(chave, 0) + 1
            _contagens[chave] = atual
            if atual > limite:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            "Limite de tentativas neste minuto foi excedido. "
                            "Aguarde até 1 minuto ou contacte suporte se o problema persistir."
                        )
                    },
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)
