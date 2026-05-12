"""POST /auth/self-service/token."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.domain.value_objects.email import normalizar_email

from . import deps, jwt_tokens
from .schemas import SelfServiceTokenRequest, SelfServiceTokenResponse

router = APIRouter()


@router.post(
    "/self-service/token",
    response_model=SelfServiceTokenResponse,
    summary="OTP → JWT self-service (gravar diagnóstico)",
    description=(
        "Consumir o código enviado por POST /auth/verificar-email/solicitar e receber um Bearer JWT "
        "válido para POST /diagnosticos/self-service (Idempotency-Key obrigatório). "
        "O e-mail do diagnóstico deve ser o mesmo verificado."
    ),
)
async def emitir_token_self_service(body: SelfServiceTokenRequest) -> SelfServiceTokenResponse:
    email_norm = normalizar_email(str(body.email))
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if not deps.codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado. Solicite um novo código.",
        )
    token, ttl_sec = jwt_tokens.create_self_service_access_token(email_norm=email_norm)
    return SelfServiceTokenResponse(access_token=token, expires_in=ttl_sec)
