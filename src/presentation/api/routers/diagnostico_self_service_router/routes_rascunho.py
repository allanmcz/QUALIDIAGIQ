"""Rascunho self-service — gravar, resumo e concluir com OTP."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status

from src.application.ports.email_service import EmailServicePort
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.email import normalizar_email
from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    inserir_leitura_publica_self_service_sync,
)
from src.infrastructure.repositories.postgres_rascunho_self_service import (
    buscar_rascunho_ativo_por_token_sync,
    inserir_rascunho_sync,
    marcar_rascunho_consumido_sync,
)
from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_email_service,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    ConcluirRascunhoDiagnosticoSelfServiceRequest,
    DiagnosticoRascunhoResumoResponse,
    DiagnosticoResponse,
    IniciarDiagnosticoRequest,
    RascunhoDiagnosticoSelfServiceResponse,
)

from . import deps

router = APIRouter()


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
    settings = deps.get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    email_norm = normalizar_email(str(payload.respondente.email))
    payload_dict = payload.model_dump(mode="json")
    try:
        token_plain, expira_em = await deps.asyncio.to_thread(
            inserir_rascunho_sync,
            dsn,
            tenant_id=tenant_ss,
            email_norm=email_norm,
            payload_dict=payload_dict,
        )
    except deps.psycopg2.Error as e:
        deps.logger.exception("rascunho_self_service_insert_falhou", erro=str(e))
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
    settings = deps.get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    row = await deps.asyncio.to_thread(
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
    cnpj_norm = ""
    if isinstance(emp, dict):
        cnpj_bruto = str(emp.get("cnpj", "") or "").strip()
        cnpj_norm = "".join(ch for ch in cnpj_bruto if ch.isdigit())
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
        empresa_cnpj=cnpj_norm,
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
    request: Request,
    body: ConcluirRascunhoDiagnosticoSelfServiceRequest,
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
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
    email_norm = str(row["email_norm"])
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
    row2 = await deps.asyncio.to_thread(
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
    if normalizar_email(str(payload.respondente.email)) != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inconsistência entre rascunho e respondente.",
        )
    tenant_ss = settings.self_service_tenant_id
    tid = getattr(request.state, "trace_id", None)
    trace_id = str(tid).strip() if tid else None
    out = await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_ss,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
        repo=repo,
        trace_id=trace_id,
        respondente_ip_origem=diagnostico_helpers.extrair_ip_cliente_http(request),
    )
    try:
        await deps.asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row2["id"])))
    except deps.psycopg2.Error as e:
        deps.logger.exception("rascunho_self_service_consumir_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico criado, mas falhou ao fechar o rascunho — contacte suporte.",
        ) from e
    try:
        leitura_plain = await deps.asyncio.to_thread(
            inserir_leitura_publica_self_service_sync,
            dsn,
            out.id,
            tenant_ss,
        )
    except deps.psycopg2.Error as e:
        deps.logger.exception("leitura_publica_self_service_insert_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico gravado, mas falhou ao emitir token de visualização — contacte suporte.",
        ) from e
    return out.model_copy(update={"leitura_token": leitura_plain})
