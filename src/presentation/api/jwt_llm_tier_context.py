"""
Extracção best-effort de contexto LLM a partir do Bearer JWT (Presentation).

Camada: Presentation — só token assinado; **nunca** tier vindo de header HTTP público (ADR-021 §2.3.2).
"""

from __future__ import annotations

import re
from typing import Any

import jwt

_RE_BEARER = re.compile(r"^Bearer(?:\s+(.*))?$", re.IGNORECASE)


def llm_tier_context_from_authorization(
    authorization_header: str | None,
    *,
    jwt_secret: str,
    algorithms: list[str],
) -> tuple[str | None, str | None]:
    """
    Devolve ``(qdi_llm_tier_claim, perfil_conta)`` do payload JWT ou ``(None, None)``.

    Args:
        authorization_header: Valor do header ``Authorization``.
        jwt_secret: Segredo HS* (Settings).
        algorithms: Algoritmos aceites (ex.: HS256).

    Returns:
        Tupla opcional para o resolver de tier (observabilidade).
    """
    if not authorization_header:
        return None, None
    raw = str(authorization_header).strip()
    m = _RE_BEARER.match(raw)
    if not m:
        return None, None
    remainder = (m.group(1) or "").strip()
    if not remainder:
        return None, None
    token = remainder.split(maxsplit=1)[0]
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            jwt_secret,
            algorithms=algorithms,
            options={"verify_signature": True},
        )
    except Exception:
        return None, None
    claim = payload.get("qdi_llm_tier")
    perfil = payload.get("perfil_conta")
    c = str(claim).strip() if claim is not None else None
    p = str(perfil).strip() if perfil is not None else None
    return (c or None), (p or None)
