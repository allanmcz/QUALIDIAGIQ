"""OTP por e-mail — `/auth/verificar-email/*`."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.ports.email_service import EmailServicePort
from src.domain.value_objects.email import normalizar_email
from src.presentation.api.dependencies import get_email_service

from . import deps
from .schemas import (
    ConfirmarVerificacaoEmailRequest,
    ConfirmarVerificacaoEmailResponse,
    SolicitarVerificacaoEmailRequest,
    SolicitarVerificacaoEmailResponse,
)

_VALIDADE_MINUTOS_CODIGO = 10

router = APIRouter()


@router.post(
    "/verificar-email/solicitar",
    response_model=SolicitarVerificacaoEmailResponse,
    summary="Solicitar código por e-mail",
    description=(
        "Envia OTP numérico para o endereço informado (SMTP configurável). "
        "Rate limit por e-mail entre reenvios. MVP: armazenamento em memória no processo da API."
    ),
)
async def solicitar_verificacao_email(
    body: SolicitarVerificacaoEmailRequest,
    email_service: Annotated[EmailServicePort, Depends(get_email_service)],
) -> SolicitarVerificacaoEmailResponse:
    settings = deps.get_settings()
    email_norm = normalizar_email(str(body.email))
    if not deps.codigo_store.pode_reenviar(email_norm):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Aguarde alguns segundos antes de pedir novo código.",
        )
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    ok = await email_service.enviar_codigo_verificacao_email(
        email_norm, codigo, _VALIDADE_MINUTOS_CODIGO
    )
    if settings.app_env == "development":
        deps.logger.info(
            "email_verificacao_codigo_dev",
            email=email_norm,
            codigo=codigo,
            smtp_ok=ok,
        )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível enviar o e-mail. Se a API roda no Docker: confira se o serviço "
                "mailpit está no ar (make dev) e SMTP_HOST=mailpit. No host: Mailpit em "
                "127.0.0.1:1025 e SMTP_HOST=127.0.0.1. Mensagens de dev: http://127.0.0.1:8025 ."
            ),
        )
    deps.codigo_store.registrar_envio(email_norm, codigo)
    return SolicitarVerificacaoEmailResponse(
        mensagem=f"Código enviado. Válido por {_VALIDADE_MINUTOS_CODIGO} minutos.",
    )


@router.post(
    "/verificar-email/confirmar",
    response_model=ConfirmarVerificacaoEmailResponse,
    summary="Confirmar código do e-mail",
)
async def confirmar_verificacao_email(
    body: ConfirmarVerificacaoEmailRequest,
) -> ConfirmarVerificacaoEmailResponse:
    email_norm = normalizar_email(str(body.email))
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if deps.codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        return ConfirmarVerificacaoEmailResponse(verificado=True)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Código inválido ou expirado. Solicite um novo código.",
    )
