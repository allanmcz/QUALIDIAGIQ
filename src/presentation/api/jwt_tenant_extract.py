"""
Extração best-effort de `tenant_id` a partir do Bearer JWT (middleware idempotência).

Camada: Presentation
"""

from __future__ import annotations

from uuid import UUID

import jwt

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
    if not raw.lower().startswith("bearer "):
        return NIL_TENANT_ID
    token = raw[7:].strip().split()[0] if raw[7:].strip() else ""
    if not token:
        return NIL_TENANT_ID
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
