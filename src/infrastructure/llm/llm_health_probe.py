"""
Probe de saúde do backend LLM (Ollama HTTP / flag router).

Camada: Infrastructure — usado por ``GET /health/llm``.
"""

from __future__ import annotations

import urllib.error
import urllib.request

from src.infrastructure.config.settings import Settings


def probe_llm_health(settings: Settings) -> dict[str, str]:
    """
    Verifica disponibilidade best-effort do LLM configurado.

    Returns:
        Dict com ``status`` ``ok`` | ``degraded`` | ``disabled`` e detalhes.
    """
    if not settings.llm_router_enabled:
        return {
            "status": "disabled",
            "router": "off",
            "backend": settings.llm_backend,
        }

    backend = settings.llm_backend.strip()
    if backend in ("anthropic", "openai", "bedrock"):
        return {"status": "ok", "router": "on", "backend": backend, "note": "cloud_api_assumed"}

    if settings.llm_bedrock_enabled:
        return {"status": "ok", "router": "on", "backend": "bedrock", "note": "bedrock_flag_on"}

    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=min(5.0, settings.ollama_timeout_seconds)) as resp:
            if resp.status == 200:
                return {
                    "status": "ok",
                    "router": "on",
                    "backend": backend,
                    "ollama": base,
                }
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {
            "status": "degraded",
            "router": "on",
            "backend": backend,
            "ollama": base,
            "error": str(e)[:200],
        }
    return {"status": "degraded", "router": "on", "backend": backend, "ollama": base}
