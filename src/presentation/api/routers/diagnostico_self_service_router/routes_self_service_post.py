"""POST /diagnosticos/self-service (JWT após OTP)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003 — FastAPI resolve Annotated/Depends em runtime

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status

from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
    get_self_service_diagnostico_claims,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import DiagnosticoResponse, IniciarDiagnosticoRequest

from . import deps

router = APIRouter()


@router.post(
    "/self-service",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar diagnóstico (e-mail verificado por OTP)",
    description=(
        "Fluxo: POST /auth/verificar-email/solicitar → POST /auth/self-service/token → este endpoint.\n\n"
        "**Bearer:** JWT self-service (claim `scope=self_service_diagnostico`).\n"
        "**Corpo:** mesmo contrato de POST /diagnosticos/. O e-mail do respondente deve coincidir com o OTP.\n"
        "**Idempotency-Key:** obrigatório."
    ),
)
async def criar_diagnostico_self_service(
    request: Request,
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    claims: Annotated[tuple[UUID, UUID, str], Depends(get_self_service_diagnostico_claims)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Persiste diagnóstico no tenant self-service (verificação de posse do e-mail)."""
    _sub, tenant_id, email_norm = claims
    payload_email = deps.codigo_store.normalizar_email(str(payload.respondente.email))
    if payload_email != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente deve ser o mesmo confirmado por OTP.",
        )
    tid = getattr(request.state, "trace_id", None)
    trace_id = str(tid).strip() if tid else None
    return await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
        repo=repo,
        trace_id=trace_id,
    )
