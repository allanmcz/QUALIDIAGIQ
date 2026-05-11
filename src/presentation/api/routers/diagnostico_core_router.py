"""
Rotas HTTP core de Diagnóstico.

Camada: Presentation
Responsabilidade: CRUD principal autenticado do diagnóstico (listar, criar, obter).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003 - tipo usado em assinatura FastAPI (runtime)

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status

from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.application.use_cases.listar_retificacoes_diagnostico import (
    ComandoListarRetificacoesDiagnostico,
    ListarRetificacoesDiagnostico,
)
from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.application.use_cases.registrar_retificacao_diagnostico import (
    ComandoRegistrarRetificacaoDiagnostico,
    RegistrarRetificacaoDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.cnpj_brasil import (
    exigir_cnpj_vazio_ou_com_dv_ok,
    normalizar_cnpj_apenas_digitos,
)
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_diagnostico_repository,
    get_listar_retificacoes_diagnostico_use_case,
    get_realizar_diagnostico_use_case,
    get_registrar_retificacao_diagnostico_use_case,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    DiagnosticoRetificacaoHttpResponse,
    IniciarDiagnosticoPainelRequest,
    RegistrarRetificacaoDiagnosticoRequest,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


def _retificacao_para_http(r: DiagnosticoRetificacaoRegisto) -> DiagnosticoRetificacaoHttpResponse:
    """Converte registo de domínio/application para schema HTTP."""
    return DiagnosticoRetificacaoHttpResponse(
        id=r.id,
        tenant_id=r.tenant_id,
        diagnostico_original_id=r.diagnostico_original_id,
        hash_diagnostico_original_sha256=r.hash_diagnostico_original_sha256,
        motivo_retificacao=r.motivo_retificacao,
        payload_retificacao=r.payload_retificacao,
        hash_retificacao_sha256=r.hash_retificacao_sha256,
        actor_user_id=r.actor_user_id,
        criado_em=r.criado_em,
    )


@router.get("/", response_model=list[DiagnosticoResumoSchema])
async def listar_diagnosticos(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    empresa_cnpj: Annotated[
        str | None,
        Query(
            description=(
                "Opcional: filtra pela coluna `empresa_cnpj` (14 dígitos, DV válido). "
                "Omite ou vazio = todos os diagnósticos do tenant."
            ),
        ),
    ] = None,
) -> list[DiagnosticoResumoSchema]:
    """Lista diagnósticos do tenant atual (ordenacao: mais recentes primeiro na camada repo/DB)."""
    _, tenant_id, _ = current
    filtro_cnpj: str | None = None
    if empresa_cnpj is not None and empresa_cnpj.strip() != "":
        norm = normalizar_cnpj_apenas_digitos(empresa_cnpj)
        if norm == "":
            filtro_cnpj = None
        else:
            try:
                exigir_cnpj_vazio_ou_com_dv_ok(norm)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=str(exc),
                ) from exc
            filtro_cnpj = norm
    rows = await repo.listar_por_tenant(
        tenant_id, limit=limit, offset=offset, empresa_cnpj=filtro_cnpj
    )
    return [diagnostico_helpers._para_resumo(d) for d in rows]


@router.post(
    "/",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar diagnóstico",
    description=(
        "Calcula o score e persiste o diagnóstico no tenant do JWT.\n\n"
        "**Headers obrigatórios:** `Authorization: Bearer <JWT>` (claim `tenant_id`) e "
        "`Idempotency-Key` (UUID v4 recomendado). Reexecução com a mesma chave devolve a mesma "
        "resposta 2xx em cache (middleware de idempotência).\n\n"
        "**Corpo:** incluir `aceite_termos_privacidade: true` (LGPD); o servidor persiste "
        "`aceite_termos_privacidade_em` (UTC) na linha do diagnóstico.\n\n"
        "**CNPJ:** obrigatório com sessão na plataforma (histórico por empresa no tenant). "
        "Fluxo só com OTP sem conta: usar rotas self-service / rascunho onde o CNPJ pode ser opcional."
    ),
)
async def criar_diagnostico(
    request: Request,
    payload: Annotated[
        IniciarDiagnosticoPainelRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Inicia um novo diagnóstico e calcula o score com base nas respostas."""
    _, tenant_id, perfil_conta = current
    tid = getattr(request.state, "trace_id", None)
    trace_id = str(tid).strip() if tid else None
    return await diagnostico_helpers._executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=perfil_conta,
        repo=repo,
        trace_id=trace_id,
        respondente_ip_origem=diagnostico_helpers.extrair_ip_cliente_http(request),
    )


@router.get(
    "/{diagnostico_id}/retificacoes",
    response_model=list[DiagnosticoRetificacaoHttpResponse],
    summary="Listar retificações do diagnóstico",
    description=(
        "Cadeia temporal append-only (ADR-012 §5). Sem UPDATE ao diagnóstico original; "
        "cada retificação referencia o hash WORM do original."
    ),
)
async def listar_retificacoes_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        ListarRetificacoesDiagnostico,
        Depends(get_listar_retificacoes_diagnostico_use_case),
    ],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[DiagnosticoRetificacaoHttpResponse]:
    """Lista retificações mais recentes primeiro."""
    _, tenant_id, _ = current
    rows = await use_case.execute(
        ComandoListarRetificacoesDiagnostico(
            tenant_id=tenant_id,
            diagnostico_original_id=diagnostico_id,
            limit=limit,
        )
    )
    return [_retificacao_para_http(x) for x in rows]


@router.post(
    "/{diagnostico_id}/retificacao",
    response_model=DiagnosticoRetificacaoHttpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registar retificação (append-only)",
    description=(
        "Exige diagnóstico **finalizado** com **hash de evidência**. "
        "Persistência apenas INSERT (cadeia de hashes). "
        "**Header:** `Idempotency-Key` (replay previsível via middleware)."
    ),
)
async def registrar_retificacao_diagnostico(
    diagnostico_id: UUID,
    payload: RegistrarRetificacaoDiagnosticoRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        RegistrarRetificacaoDiagnostico,
        Depends(get_registrar_retificacao_diagnostico_use_case),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> DiagnosticoRetificacaoHttpResponse:
    """Regista nova retificação na cadeia auditável."""
    _ = idempotency_key
    user_id, tenant_id, _ = current
    try:
        r = await use_case.execute(
            ComandoRegistrarRetificacaoDiagnostico(
                tenant_id=tenant_id,
                actor_user_id=user_id,
                diagnostico_original_id=diagnostico_id,
                motivo_retificacao=payload.motivo_retificacao,
                payload_retificacao=payload.payload_retificacao,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _retificacao_para_http(r)


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obter_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Busca um diagnóstico pelo ID, garantindo o isolamento do tenant."""
    _, tenant_id, _ = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    return await diagnostico_helpers._montar_diagnostico_response(repo, diagnostico)
