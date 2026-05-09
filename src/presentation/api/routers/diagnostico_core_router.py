"""
Rotas HTTP core de Diagnóstico.

Camada: Presentation
Responsabilidade: CRUD principal autenticado do diagnóstico (listar, criar, obter).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003 - tipo usado em assinatura FastAPI (runtime)

from fastapi import APIRouter, Body, Depends, Query, Request, status

from src.application.use_cases.realizar_diagnostico import RealizarDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    IniciarDiagnosticoRequest,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


@router.get("/", response_model=list[DiagnosticoResumoSchema])
async def listar_diagnosticos(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DiagnosticoResumoSchema]:
    """Lista diagnósticos do tenant atual (ordenacao: mais recentes primeiro na camada repo/DB)."""
    _, tenant_id, _ = current
    rows = await repo.listar_por_tenant(tenant_id, limit=limit, offset=offset)
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
        "`aceite_termos_privacidade_em` (UTC) na linha do diagnóstico."
    ),
)
async def criar_diagnostico(
    request: Request,
    payload: Annotated[
        IniciarDiagnosticoRequest,
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
    )


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
