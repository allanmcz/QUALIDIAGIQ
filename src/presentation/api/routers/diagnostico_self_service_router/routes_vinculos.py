"""Vinculação de rascunho à conta, leitura pública e leads self-service."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    ComandoVincularDiagnosticosLeadSelfService,
    VincularDiagnosticosLeadSelfService,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    buscar_diagnostico_conclusao_publica_sync,
)
from src.infrastructure.repositories.postgres_rascunho_self_service import (
    buscar_rascunho_ativo_por_token_sync,
    marcar_rascunho_consumido_sync,
)
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
    get_vincular_diagnosticos_lead_self_service_use_case,
)
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    DiagnosticoConclusaoSelfServicePublicoResponse,
    DiagnosticoResponse,
    IniciarDiagnosticoRequest,
    VincularLeadsSelfServiceResponse,
    VincularRascunhoContaPlataformaRequest,
)

from . import deps

router = APIRouter()


@router.post(
    "/rascunho-self-service/vincular-conta",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Materializar rascunho no tenant da conta (JWT)",
    description=(
        "Exige **Bearer** da conta na plataforma. O e-mail do respondente no rascunho deve ser **igual** "
        "ao e-mail do admin (LGPD / prova de posse). **Idempotency-Key** obrigatório."
    ),
)
async def vincular_rascunho_conta_plataforma(
    request: Request,
    body: VincularRascunhoContaPlataformaRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    user_id, tenant_id, perfil_conta = current
    settings = deps.get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    row = await deps.asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    try:
        email_admin = deps.buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except deps.psycopg2.Error as e:
        deps.logger.exception("vincular_rascunho_email_lookup_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o consultor no PostgreSQL.",
        ) from e
    if not email_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não corresponde a um consultor com e-mail resolvível.",
        )
    email_admin_norm = deps.codigo_store.normalizar_email(email_admin)
    pj = diagnostico_helpers._payload_json_como_dict(row.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    payload = IniciarDiagnosticoRequest.model_validate(pj)
    email_resp = deps.codigo_store.normalizar_email(str(payload.respondente.email))
    if email_resp != email_admin_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente no rascunho deve ser o mesmo da sua conta na plataforma.",
        )
    tid = getattr(request.state, "trace_id", None)
    trace_id = str(tid).strip() if tid else None
    out = await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=perfil_conta,
        repo=repo,
        trace_id=trace_id,
        respondente_ip_origem=diagnostico_helpers.extrair_ip_cliente_http(request),
    )
    try:
        await deps.asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row["id"])))
    except deps.psycopg2.Error as e:
        deps.logger.exception("vincular_rascunho_consumir_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico criado, mas falhou ao fechar o rascunho — contacte suporte.",
        ) from e
    return out


@router.get(
    "/self-service/conclusao-visualizacao",
    response_model=DiagnosticoConclusaoSelfServicePublicoResponse,
    summary="Visualização pública do diagnóstico concluído (self-service)",
    description=(
        "Endpoint **público** (sem JWT). Exige ``diagnostico_id`` e ``leitura_token`` devolvidos por "
        "**POST /diagnosticos/rascunho-self-service/concluir** (token persistido em PostgreSQL, TTL ~7 dias). "
        "Não expõe checklist/PDF — apenas snapshot executivo alinhado à página de conclusão."
    ),
)
async def obter_conclusao_self_service_publica(
    diagnostico_id: Annotated[
        UUID, Query(description="UUID do diagnóstico gravado no tenant self-service.")
    ],
    leitura_token: Annotated[
        str,
        Query(
            min_length=16,
            description="Token opaco devolvido no campo `leitura_token` da resposta de concluir.",
        ),
    ],
) -> DiagnosticoConclusaoSelfServicePublicoResponse:
    """Lê diagnóstico da BD após validar o token de leitura (sem armazenamento no navegador como fonte)."""
    settings = deps.get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    row = await deps.asyncio.to_thread(
        buscar_diagnostico_conclusao_publica_sync,
        dsn,
        diagnostico_id=diagnostico_id,
        tenant_id_esperado=tenant_ss,
        token_plain=leitura_token.strip(),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnóstico não encontrado ou token inválido/expirado.",
        )
    return diagnostico_helpers._conclusao_publica_row_para_schema(row)


@router.post(
    "/vincular-leads-self-service",
    response_model=VincularLeadsSelfServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Vincular diagnósticos gratuitos (self-service) ao tenant da conta na plataforma",
    description=(
        "Reatribui ao tenant do JWT as linhas em `diagnosticos` gravadas no tenant self-service "
        "(fluxo OTP), com `respondente_email` igual ao e-mail do consultor em `admins` e plano gratuito. "
        "Resolve o caso em que o lead concluiu o assistente antes de iniciar sessão no painel. "
        "**Idempotency-Key** obrigatório (mesmo middleware dos outros POST sob `/diagnosticos/`)."
    ),
)
async def vincular_leads_self_service(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        VincularDiagnosticosLeadSelfService,
        Depends(get_vincular_diagnosticos_lead_self_service_use_case),
    ],
) -> VincularLeadsSelfServiceResponse:
    """Move diagnósticos do pool OTP para o tenant do token (LGPD: e-mail conferido em `admins`)."""
    user_id, tenant_id, _perfil = current
    settings = deps.get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API para validar o consultor.",
        )
    try:
        email = deps.buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except deps.psycopg2.Error as e:
        deps.logger.exception("vincular_leads_email_lookup_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o consultor no PostgreSQL.",
        ) from e
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não corresponde a um consultor com e-mail resolvível para vinculação.",
        )
    comando = ComandoVincularDiagnosticosLeadSelfService(
        email_admin_normalizado=deps.codigo_store.normalizar_email(email),
        tenant_destino=tenant_id,
        tenant_self_service=settings.self_service_tenant_id,
    )
    try:
        ids = await use_case.execute(comando)
    except deps.psycopg2.Error as e:
        deps.logger.exception("vincular_leads_update_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar diagnósticos no PostgreSQL.",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return VincularLeadsSelfServiceResponse(total_vinculados=len(ids), diagnostico_ids=ids)
