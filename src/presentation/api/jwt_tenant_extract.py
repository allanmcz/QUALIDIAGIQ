"""
Extração best-effort de `tenant_id` a partir do Bearer JWT (middleware idempotência).

Camada: Presentation
"""

from __future__ import annotations

import re
from uuid import UUID

import jwt

# Exige palavra ``Bearer`` isolada: ``Bearer`` sozinho ou ``Bearer`` + whitespace + jwt.
# Rejeita ``BearerToken`` (sem espaço), coerente com o prefixo ``bearer `` do parser legado.
_RE_BEARER = re.compile(r"^Bearer(?:\s+(.*))?$", re.IGNORECASE)

NIL_TENANT_ID = UUID("00000000-0000-0000-0000-000000000000")


def tenant_id_from_bearer_authorization(
    authorization_header: str | None,
    jwt_secret: str,
    algorithms: list[str],
) -> UUID:
    """
    Decodifica JWT com verificação de assinatura e devolve tenant_id ou NIL_TENANT_ID.

    Args:
        authorization_header: Valor bruto do header Authorization.
        jwt_secret: Segredo HS*.
        algorithms: Algoritmos aceitos (ex.: HS256).

    Returns:
        UUID do tenant ou NIL_TENANT_ID se ausente ou inválido.
    """
    if not authorization_header:
        return NIL_TENANT_ID
    raw = str(authorization_header).strip()
    m = _RE_BEARER.match(raw)
    if not m:
        return NIL_TENANT_ID
    remainder = (m.group(1) or "").strip()
    if not remainder:
        return NIL_TENANT_ID
    token = remainder.split(maxsplit=1)[0]
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=algorithms,
            options={"verify_signature": True},
        )
        tid = payload.get("tenant_id")
        if tid:
            return UUID(str(tid))
    except Exception:
        return NIL_TENANT_ID
    return NIL_TENANT_ID
