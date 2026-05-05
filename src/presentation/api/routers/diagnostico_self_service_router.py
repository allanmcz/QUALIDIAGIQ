"""
Rotas HTTP de self-service para Diagnóstico.

Camada: Presentation
Responsabilidade: fluxo sem sessão na plataforma (rascunho + OTP + conclusão + vinculação).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import psycopg2
import structlog
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status

from src.application.ports.email_service import EmailServicePort
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    ComandoVincularDiagnosticosLeadSelfService,
    VincularDiagnosticosLeadSelfService,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.auth.postgres_admin_login import buscar_email_admin_por_id_e_tenant_postgres
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    buscar_diagnostico_conclusao_publica_sync,
    inserir_leitura_publica_self_service_sync,
)
from src.infrastructure.repositories.postgres_rascunho_self_service import (
    buscar_rascunho_ativo_por_token_sync,
    inserir_rascunho_sync,
    marcar_rascunho_consumido_sync,
)
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_diagnostico_repository,
    get_email_service,
    get_realizar_diagnostico_use_case,
    get_self_service_diagnostico_claims,
    get_vincular_diagnosticos_lead_self_service_use_case,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    ConcluirRascunhoDiagnosticoSelfServiceRequest,
    DiagnosticoConclusaoSelfServicePublicoResponse,
    DiagnosticoRascunhoResumoResponse,
    DiagnosticoResponse,
    IniciarDiagnosticoRequest,
    RascunhoDiagnosticoSelfServiceResponse,
    VincularLeadsSelfServiceResponse,
    VincularRascunhoContaPlataformaRequest,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])
logger = structlog.get_logger(__name__)


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
    payload_email = codigo_store.normalizar_email(str(payload.respondente.email))
    if payload_email != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente deve ser o mesmo confirmado por OTP.",
        )
    return await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
        repo=repo,
    )


@router.post(
    "/rascunho-self-service",
    response_model=RascunhoDiagnosticoSelfServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gravar rascunho do diagnóstico na base (antes do OTP)",
    description=(
        "Persiste o mesmo corpo de **POST /diagnosticos/self-service** na tabela de rascunhos e envia OTP. "
        "O cliente deve guardar apenas o **resgate_token** (fragmento de URL ou memória de curto prazo) — "
        "não usar o payload completo em sessionStorage como etapa final. "
        "**Idempotency-Key** obrigatório (middleware)."
    ),
)
async def criar_rascunho_diagnostico_self_service(
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    email_service: Annotated[EmailServicePort, Depends(get_email_service)],
) -> RascunhoDiagnosticoSelfServiceResponse:
    """Grava JSON do assistente no Postgres (tenant self-service) e dispara verificação de e-mail."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    email_norm = codigo_store.normalizar_email(str(payload.respondente.email))
    payload_dict = payload.model_dump(mode="json")
    try:
        token_plain, expira_em = await asyncio.to_thread(
            inserir_rascunho_sync,
            dsn,
            tenant_id=tenant_ss,
            email_norm=email_norm,
            payload_dict=payload_dict,
        )
    except psycopg2.Error as e:
        logger.exception("rascunho_self_service_insert_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível gravar o rascunho no PostgreSQL.",
        ) from e

    mensagem = await diagnostico_helpers._enviar_otp_verificacao_para_email(
        email_norm, email_service
    )
    return RascunhoDiagnosticoSelfServiceResponse(
        resgate_token=token_plain,
        mensagem=mensagem,
        expira_em=expira_em if expira_em.tzinfo else expira_em.replace(tzinfo=UTC),
    )


@router.get(
    "/rascunho-self-service/resumo",
    response_model=DiagnosticoRascunhoResumoResponse,
    summary="Resumo do rascunho (token opaco)",
    description=(
        "Metadados mínimos para a página de confirmação. **Header obrigatório:** "
        "`X-Rascunho-Token` com o valor devolvido por POST /diagnosticos/rascunho-self-service."
    ),
)
async def resumo_rascunho_diagnostico_self_service(
    x_rascunho_token: Annotated[str, Header(alias="X-Rascunho-Token")],
) -> DiagnosticoRascunhoResumoResponse:
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, x_rascunho_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    pj = diagnostico_helpers._payload_json_como_dict(row.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    emp = pj.get("empresa")
    razao = (
        str(emp.get("razao_social", "")).strip() if isinstance(emp, dict) else ""
    ) or "(sem razão social)"
    email_norm = str(row.get("email_norm") or "").strip()
    exp_raw = row.get("expira_em")
    if exp_raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    exp_dt = (
        exp_raw
        if isinstance(exp_raw, datetime)
        else datetime.fromisoformat(str(exp_raw).replace("Z", "+00:00"))
    )
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=UTC)
    return DiagnosticoRascunhoResumoResponse(
        empresa_razao_social=razao,
        email_mascarado=diagnostico_helpers._mascarar_email_norm(email_norm),
        respondente_email=str(email_norm),
        expira_em=exp_dt,
    )


@router.post(
    "/rascunho-self-service/concluir",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Concluir rascunho com OTP (grava diagnóstico final)",
    description=(
        "Valida o código enviado por e-mail, materializa **POST /diagnosticos/self-service** a partir "
        "do JSON guardado no rascunho e marca o rascunho como consumido. **Idempotency-Key** obrigatório."
    ),
)
async def concluir_rascunho_diagnostico_self_service(
    body: ConcluirRascunhoDiagnosticoSelfServiceRequest,
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    email_norm = str(row["email_norm"])
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if not codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado. Solicite um novo código.",
        )
    row2 = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    pj = diagnostico_helpers._payload_json_como_dict(row2.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    payload = IniciarDiagnosticoRequest.model_validate(pj)
    if codigo_store.normalizar_email(str(payload.respondente.email)) != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inconsistência entre rascunho e respondente.",
        )
    tenant_ss = settings.self_service_tenant_id
    out = await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_ss,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
        repo=repo,
    )
    try:
        await asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row2["id"])))
    except psycopg2.Error as e:
        logger.exception("rascunho_self_service_consumir_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico criado, mas falhou ao fechar o rascunho — contacte suporte.",
        ) from e
    try:
        leitura_plain = await asyncio.to_thread(
            inserir_leitura_publica_self_service_sync,
            dsn,
            out.id,
            tenant_ss,
        )
    except psycopg2.Error as e:
        logger.exception("leitura_publica_self_service_insert_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico gravado, mas falhou ao emitir token de visualização — contacte suporte.",
        ) from e
    return out.model_copy(update={"leitura_token": leitura_plain})


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
    body: VincularRascunhoContaPlataformaRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    user_id, tenant_id, perfil_conta = current
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    try:
        email_admin = buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except psycopg2.Error as e:
        logger.exception("vincular_rascunho_email_lookup_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o consultor no PostgreSQL.",
        ) from e
    if not email_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não corresponde a um consultor com e-mail resolvível.",
        )
    email_admin_norm = codigo_store.normalizar_email(email_admin)
    pj = diagnostico_helpers._payload_json_como_dict(row.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    payload = IniciarDiagnosticoRequest.model_validate(pj)
    email_resp = codigo_store.normalizar_email(str(payload.respondente.email))
    if email_resp != email_admin_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente no rascunho deve ser o mesmo da sua conta na plataforma.",
        )
    out = await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=perfil_conta,
        repo=repo,
    )
    try:
        await asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row["id"])))
    except psycopg2.Error as e:
        logger.exception("vincular_rascunho_consumir_falhou", erro=str(e))
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
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    row = await asyncio.to_thread(
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
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API para validar o consultor.",
        )
    try:
        email = buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except psycopg2.Error as e:
        logger.exception("vincular_leads_email_lookup_falhou", erro=str(e))
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
        email_admin_normalizado=codigo_store.normalizar_email(email),
        tenant_destino=tenant_id,
        tenant_self_service=settings.self_service_tenant_id,
    )
    try:
        ids = await use_case.execute(comando)
    except psycopg2.Error as e:
        logger.exception("vincular_leads_update_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar diagnósticos no PostgreSQL.",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return VincularLeadsSelfServiceResponse(total_vinculados=len(ids), diagnostico_ids=ids)
