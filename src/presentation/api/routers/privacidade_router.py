"""
Rotas HTTP para solicitações LGPD do titular.

Camada: Presentation
Responsabilidade: roteamento, validação Pydantic e conversão para casos de uso.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003 - tipo usado em assinatura FastAPI (runtime)

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import Response

from src.application.errors import EliminacaoDiagnosticoFinalizadoWormError
from src.application.ports.lgpd_titular_solicitacao_port import (
    CanalSolicitacaoTitular,
    StatusSolicitacaoTitular,
    TipoSolicitacaoTitular,
)
from src.application.use_cases.atualizar_status_solicitacao_titular_lgpd import (
    AtualizarStatusSolicitacaoTitularLgpd,
    ComandoAtualizarStatusSolicitacaoTitularLgpd,
)
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ComandoExecutarAnonimizacaoRespondenteLgpd,
    ExecutarAnonimizacaoRespondenteLgpd,
)
from src.application.use_cases.executar_eliminacao_diagnostico_lgpd import (
    ComandoExecutarEliminacaoDiagnosticoLgpd,
    ExecutarEliminacaoDiagnosticoLgpd,
)
from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    ComandoGerarExportPortabilidadeDiagnostico,
    GerarExportPortabilidadeDiagnostico,
)
from src.application.use_cases.listar_solicitacao_titular_lgpd import (
    ComandoListarSolicitacaoTitularLgpd,
    ListarSolicitacaoTitularLgpd,
)
from src.application.use_cases.registrar_solicitacao_titular_lgpd import (
    ComandoRegistrarSolicitacaoTitularLgpd,
    RegistrarSolicitacaoTitularLgpd,
)
from src.presentation.api.dependencies import (
    get_atualizar_status_solicitacao_titular_lgpd_use_case,
    get_current_user_tenant,
    get_executar_anonimizacao_respondente_lgpd_use_case,
    get_executar_eliminacao_diagnostico_lgpd_use_case,
    get_gerar_export_portabilidade_diagnostico_use_case,
    get_listar_solicitacao_titular_lgpd_use_case,
    get_registrar_solicitacao_titular_lgpd_use_case,
)
from src.presentation.api.schemas import (
    AnonimizarRespondenteLgpdHttpRequest,
    AnonimizarRespondenteLgpdHttpResponse,
    AtualizarStatusSolicitacaoTitularLgpdRequest,
    EliminarDiagnosticoLgpdHttpRequest,
    EliminarDiagnosticoLgpdHttpResponse,
    FormatoExportPortabilidade,
    RegistrarSolicitacaoTitularLgpdRequest,
    SolicitacaoTitularLgpdResponse,
)

router = APIRouter(prefix="/privacidade", tags=["Privacidade LGPD"])


def _parse_tipo(raw: str) -> TipoSolicitacaoTitular:
    try:
        return TipoSolicitacaoTitular(raw.strip().lower())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo LGPD inválido.",
        ) from e


def _parse_canal(raw: str) -> CanalSolicitacaoTitular:
    try:
        return CanalSolicitacaoTitular(raw.strip().lower())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Canal LGPD inválido.",
        ) from e


def _parse_status(raw: str) -> StatusSolicitacaoTitular:
    try:
        return StatusSolicitacaoTitular(raw.strip().lower())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status LGPD inválido.",
        ) from e


def _to_response(model: object) -> SolicitacaoTitularLgpdResponse:
    from src.application.ports.lgpd_titular_solicitacao_port import SolicitacaoTitular

    row = model
    if not isinstance(row, SolicitacaoTitular):
        raise TypeError("Modelo de solicitação LGPD inválido.")
    return SolicitacaoTitularLgpdResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        diagnostico_id=row.diagnostico_id,
        tipo=row.tipo.value,
        status=row.status.value,
        canal=row.canal.value,
        solicitante_email=row.solicitante_email,
        payload=dict(row.payload),
        observacao_interna=row.observacao_interna,
        actor_user_id=row.actor_user_id,
        criado_em=row.criado_em,
        atualizado_em=row.atualizado_em,
    )


@router.post(
    "/solicitacoes",
    response_model=SolicitacaoTitularLgpdResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar solicitação LGPD do titular",
    description=(
        "Abre solicitação operacional do art. 18 (acesso, correção, anonimização, eliminação, "
        "portabilidade, oposição) no tenant do JWT. Requer header Idempotency-Key."
    ),
)
async def registrar_solicitacao_lgpd(
    payload: RegistrarSolicitacaoTitularLgpdRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        RegistrarSolicitacaoTitularLgpd,
        Depends(get_registrar_solicitacao_titular_lgpd_use_case),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> SolicitacaoTitularLgpdResponse:
    """POST de solicitação LGPD por tenant autenticado."""
    _ = idempotency_key
    user_id, tenant_id, _ = current
    cmd = ComandoRegistrarSolicitacaoTitularLgpd(
        tenant_id=tenant_id,
        diagnostico_id=payload.diagnostico_id,
        tipo=_parse_tipo(payload.tipo),
        canal=_parse_canal(payload.canal),
        solicitante_email=payload.solicitante_email,
        payload=payload.payload.model_dump(mode="json", exclude_none=True),
        actor_user_id=user_id,
    )
    try:
        created = await use_case.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return _to_response(created)


@router.get(
    "/solicitacoes",
    response_model=list[SolicitacaoTitularLgpdResponse],
    summary="Listar solicitações LGPD do tenant",
    description="Lista solicitações do tenant autenticado, com filtro opcional por status.",
)
async def listar_solicitacoes_lgpd(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        ListarSolicitacaoTitularLgpd,
        Depends(get_listar_solicitacao_titular_lgpd_use_case),
    ],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[SolicitacaoTitularLgpdResponse]:
    """GET paginado de solicitações LGPD no tenant do JWT."""
    _, tenant_id, _ = current
    status_enum = _parse_status(status_filter) if status_filter else None
    rows = await use_case.execute(
        ComandoListarSolicitacaoTitularLgpd(
            tenant_id=tenant_id,
            status=status_enum,
            limit=limit,
        )
    )
    return [_to_response(row) for row in rows]


@router.patch(
    "/solicitacoes/{solicitacao_id}/status",
    response_model=SolicitacaoTitularLgpdResponse,
    summary="Atualizar status de solicitação LGPD",
    description="Atualiza status operacional (backoffice) da solicitação no tenant autenticado.",
)
async def atualizar_status_solicitacao_lgpd(
    solicitacao_id: UUID,
    payload: AtualizarStatusSolicitacaoTitularLgpdRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarStatusSolicitacaoTitularLgpd,
        Depends(get_atualizar_status_solicitacao_titular_lgpd_use_case),
    ],
) -> SolicitacaoTitularLgpdResponse:
    """PATCH de status da solicitação LGPD por tenant."""
    user_id, tenant_id, _ = current
    updated = await use_case.execute(
        ComandoAtualizarStatusSolicitacaoTitularLgpd(
            tenant_id=tenant_id,
            solicitacao_id=solicitacao_id,
            status=_parse_status(payload.status),
            observacao_interna=payload.observacao_interna,
            actor_user_id=user_id,
        )
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada"
        )
    return _to_response(updated)


@router.post(
    "/diagnosticos/{diagnostico_id}/anonimizar-respondente",
    response_model=AnonimizarRespondenteLgpdHttpResponse,
    summary="Executar anonimização de PII do respondente",
    description=(
        "Exige solicitação LGPD ``anonimizacao`` com status ``deferida`` ligada ao mesmo "
        "``diagnostico_id``. Regista ``lgpd_anonimizacao_log`` e aplica padrão autorizado pelo "
        "WORM (email sentinel, nome marcador, remoção de cargo/telefone)."
    ),
)
async def anonimizar_respondente_lgpd(
    diagnostico_id: UUID,
    payload: AnonimizarRespondenteLgpdHttpRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        ExecutarAnonimizacaoRespondenteLgpd,
        Depends(get_executar_anonimizacao_respondente_lgpd_use_case),
    ],
) -> AnonimizarRespondenteLgpdHttpResponse:
    user_id, tenant_id, _ = current
    try:
        await use_case.execute(
            ComandoExecutarAnonimizacaoRespondenteLgpd(
                tenant_id=tenant_id,
                actor_user_id=user_id,
                diagnostico_id=diagnostico_id,
                solicitacao_id=payload.solicitacao_id,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return AnonimizarRespondenteLgpdHttpResponse(
        diagnostico_id=diagnostico_id,
        solicitacao_id=payload.solicitacao_id,
    )


@router.post(
    "/diagnosticos/{diagnostico_id}/eliminar-diagnostico",
    response_model=EliminarDiagnosticoLgpdHttpResponse,
    summary="Eliminar diagnóstico fisicamente (LGPD — pré-finalização)",
    description=(
        "Exige solicitação LGPD ``eliminacao`` com status ``deferida`` ligada ao mesmo "
        "``diagnostico_id``. Remove a linha apenas se o diagnóstico **não** estiver "
        "``finalizado`` (WORM). Se ``finalizado``, responde **422** orientando anonimização."
    ),
)
async def eliminar_diagnostico_lgpd(
    diagnostico_id: UUID,
    payload: EliminarDiagnosticoLgpdHttpRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        ExecutarEliminacaoDiagnosticoLgpd,
        Depends(get_executar_eliminacao_diagnostico_lgpd_use_case),
    ],
) -> EliminarDiagnosticoLgpdHttpResponse:
    """DELETE físico do agregado quando ainda não há evidência finalizada (decisão J4 DEV_09052026_V2)."""
    user_id, tenant_id, _ = current
    try:
        await use_case.execute(
            ComandoExecutarEliminacaoDiagnosticoLgpd(
                tenant_id=tenant_id,
                actor_user_id=user_id,
                diagnostico_id=diagnostico_id,
                solicitacao_id=payload.solicitacao_id,
            )
        )
    except EliminacaoDiagnosticoFinalizadoWormError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return EliminarDiagnosticoLgpdHttpResponse(
        diagnostico_id=diagnostico_id,
        solicitacao_id=payload.solicitacao_id,
    )


@router.get(
    "/diagnosticos/{diagnostico_id}/export-portabilidade",
    summary="Exportar pacote de portabilidade (JSON ou PDF com JSON embebido)",
    description=(
        "Exige solicitação LGPD tipo **portabilidade** com status **deferida** referente ao mesmo "
        "`diagnostico_id`. Formato **pacote_pdf**: PDF humano com anexo "
        "`qdi-diagnostico-export-v1.json` (ADR-012 §4)."
    ),
    response_class=Response,
)
async def export_portabilidade_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        GerarExportPortabilidadeDiagnostico,
        Depends(get_gerar_export_portabilidade_diagnostico_use_case),
    ],
    solicitacao_id: Annotated[
        UUID,
        Query(description="UUID da solicitação LGPD (tipo portabilidade, status deferida)."),
    ],
    formato: Annotated[
        FormatoExportPortabilidade,
        Query(description="json (default) ou pacote_pdf (PDF com anexo JSON)."),
    ] = FormatoExportPortabilidade.json,
) -> Response:
    """Gera JSON validado por schema ou PDF com anexo (machine-readable embutido)."""
    _, tenant_id, _ = current
    try:
        resultado = await use_case.execute(
            ComandoGerarExportPortabilidadeDiagnostico(
                tenant_id=tenant_id,
                diagnostico_id=diagnostico_id,
                solicitacao_id=solicitacao_id,
                gerar_pdf_anexo=(formato == FormatoExportPortabilidade.pacote_pdf),
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if formato == FormatoExportPortabilidade.pacote_pdf:
        if resultado.pdf_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao gerar PDF de portabilidade.",
            )
        nome = f"qdi-portabilidade-{diagnostico_id}.pdf"
        return Response(
            content=resultado.pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nome}"'},
        )

    nome_j = "qdi-diagnostico-export-v1.json"
    return Response(
        content=resultado.json_utf8,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nome_j}"'},
    )
