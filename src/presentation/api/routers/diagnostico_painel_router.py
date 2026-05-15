"""
Rotas HTTP autenticadas — mutações do painel sobre diagnóstico finalizado.

Camada: Presentation
Responsabilidade: M12, quadro de implantação, subtarefas do plano, explicação LLM do score e anexo de PDF (lock otimista).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.services.explicacao_score_contexto import (
    montar_campos_extras_explicacao_score,
    snapshot_explicacao_score_llm_de_resposta,
)
from src.application.services.explicacao_score_llm_acesso import (
    mensagem_acesso_negado_explicacao_score_llm,
    pode_gerar_explicacao_score_llm,
)
from src.application.use_cases.anexar_relatorio_otimista import (
    AnexarRelatorioOtimista,
    ComandoAnexarRelatorioOtimista,
)
from src.application.use_cases.atualizar_checklist_m12_autoconf import (
    AtualizarChecklistM12Autoconf,
    ComandoAtualizarChecklistM12Autoconf,
)
from src.application.use_cases.atualizar_quadro_implantacao import (
    AtualizarQuadroImplantacao,
    ComandoAtualizarQuadroImplantacao,
)
from src.application.use_cases.explicar_score_llm_use_case import (
    ComandoExplicarScoreLlm,
    ExplicarScoreLlmUseCase,
)
from src.application.use_cases.plano_painel_subtarefa import (
    AtualizarSubtarefaPlanoDiagnostico,
    ComandoAtualizarSubtarefaPlanoDiagnostico,
    ComandoCriarSubtarefaPlanoDiagnostico,
    CriarSubtarefaPlanoDiagnostico,
)
from src.domain.entities.diagnostico import StatusDiagnostico
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.llm_quota_service import (
    LlmQuotaExcedidaError,
    assert_quota_disponivel_sync,
    registrar_uso_llm_sync,
)
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_atualizar_checklist_m12_autoconf_use_case,
    get_atualizar_quadro_implantacao_use_case,
    get_atualizar_subtarefa_plano_diagnostico_use_case,
    get_criar_subtarefa_plano_diagnostico_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_explicar_score_llm_use_case,
)
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    CriarSubtarefaPlanoDiagnosticoRequest,
    DiagnosticoResponse,
    ExplicacaoScoreLlmHistoricoListaSchema,
    ExplicacaoScoreLlmPersistidaSchema,
    PatchChecklistM12AutoconfRequest,
    PatchQuadroImplantacaoRequest,
    PatchRelatorioPdfRequest,
    PatchSubtarefaPlanoDiagnosticoRequest,
)

router = APIRouter()


@router.patch(
    "/{diagnostico_id}/checklist-m12-autoconf",
    response_model=DiagnosticoResponse,
    summary="Atualizar autoconf ABNT M12",
    description=(
        "Persiste os 10 valores Likert (1-5) da autoconferência (ABNT NBR 17301). "
        "Exige diagnóstico **finalizado** e header **If-Match** com `versao_otimista` atual."
    ),
)
async def atualizar_checklist_m12_autoconf(
    diagnostico_id: UUID,
    payload: PatchChecklistM12AutoconfRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarChecklistM12Autoconf,
        Depends(get_atualizar_checklist_m12_autoconf_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """PATCH M12 — lock otimista alinhado ao PATCH de relatório PDF."""
    user_id, tenant_id, perfil_conta = current
    try:
        versao = diagnostico_helpers._parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        checklist_m12_autoconf=list(payload.checklist_m12_autoconf),
        versao_esperada=versao,
        actor_user_id=user_id,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return await diagnostico_helpers._montar_diagnostico_response(
        repo, atualizado, perfil_conta=perfil_conta
    )


@router.patch(
    "/{diagnostico_id}/quadro-implantacao-anotacoes",
    response_model=DiagnosticoResponse,
    summary="Atualizar anotações do quadro de implantação",
    description=(
        "Mescla no mapa persistido as chaves enviadas (meta de prazo ISO, comentários e, opcionalmente, "
        "``descricao_personalizada`` que substitui o texto canônico da ação no painel). "
        "Chaves não enviadas permanecem inalteradas; por chave, campos ausentes no PATCH preservam valores já "
        "gravados. Chave: ``f{índice_frente}_a{índice_ação}`` (legado) ou **UUID** ``plano_acao_id``. "
        "Campo legado ``comentario`` (único) ainda é aceito. Exige diagnóstico **finalizado** e **If-Match**."
    ),
)
async def atualizar_quadro_implantacao_anotacoes(
    diagnostico_id: UUID,
    payload: PatchQuadroImplantacaoRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarQuadroImplantacao,
        Depends(get_atualizar_quadro_implantacao_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """PATCH quadro — lock otimista (mesmo contrato do M12)."""
    user_id, tenant_id, perfil_conta = current
    try:
        versao = diagnostico_helpers._parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    blob: dict[str, dict[str, Any]] = {}
    for k, v in payload.quadro_implantacao_anotacoes.items():
        # ``QuadroImplantacaoAnotacaoItemSchema`` já promove ``comentario`` legado para ``comentarios``.
        coms = list(v.comentarios)
        blob[k] = {
            "prazo_meta": v.prazo_meta,
            "comentarios": coms,
            "descricao_personalizada": v.descricao_personalizada.strip(),
        }
    comando = ComandoAtualizarQuadroImplantacao(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        quadro_implantacao_anotacoes=blob,
        versao_esperada=versao,
        actor_user_id=user_id,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return await diagnostico_helpers._montar_diagnostico_response(
        repo, atualizado, perfil_conta=perfil_conta
    )


@router.post(
    "/{diagnostico_id}/explicacao-score-llm",
    response_model=ExplicacaoScoreLlmPersistidaSchema,
    summary="Explicar score via LLM (painel)",
    description=(
        "Gera narrativa sobre o **score geral já calculado** (motor determinístico). "
        "Exige diagnóstico **finalizado** com ``score_geral`` persistido. "
        "**Idempotency-Key** obrigatório (middleware — replay de resposta 2xx)."
    ),
)
async def explicar_score_llm_painel(
    diagnostico_id: UUID,
    request: Request,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    use_case: Annotated[ExplicarScoreLlmUseCase, Depends(get_explicar_score_llm_use_case)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> ExplicacaoScoreLlmPersistidaSchema:
    """POST painel — delega a ``ExplicarScoreLlmUseCase`` e persiste snapshot JSONB."""
    user_id, tenant_id, perfil_conta = current
    raw_key = (idempotency_key or "").strip()
    d = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    if d.status != StatusDiagnostico.FINALIZADO or d.score_geral is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Só é possível explicar o score para diagnóstico finalizado com score persistido.",
        )
    if not pode_gerar_explicacao_score_llm(perfil_conta, d):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensagem_acesso_negado_explicacao_score_llm(),
        )
    settings = get_settings()
    dsn = settings.sync_database_url
    if dsn and settings.llm_quota_explicacao_score_daily > 0:
        try:
            await asyncio.to_thread(
                assert_quota_disponivel_sync,
                dsn,
                tenant_id=tenant_id,
                task_type="explicacao_score",
                limite_diario=settings.llm_quota_explicacao_score_daily,
            )
        except LlmQuotaExcedidaError as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
            ) from e
    tid_trace = getattr(request.state, "trace_id", None)
    trace_log = str(tid_trace).strip() if tid_trace else str(uuid4())
    cmd = ComandoExplicarScoreLlm(
        tenant_id=tenant_id,
        trace_id=trace_log,
        score_geral=float(d.score_geral),
        campos_extras=montar_campos_extras_explicacao_score(d),
        idempotency_key=raw_key[:128] if raw_key else None,
    )
    try:
        out = await use_case.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    gerado_em = datetime.now(UTC)
    snapshot = snapshot_explicacao_score_llm_de_resposta(
        out, trace_id=trace_log, gerado_em_iso=gerado_em.isoformat()
    )
    try:
        await repo.atualizar_explicacao_score_llm(diagnostico_id, tenant_id, snapshot)
        await repo.registrar_explicacao_score_llm_historico(
            diagnostico_id,
            tenant_id,
            snapshot,
            actor_user_id=user_id,
            trace_id=trace_log,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    if dsn:
        await asyncio.to_thread(
            registrar_uso_llm_sync,
            dsn,
            tenant_id=tenant_id,
            task_type="explicacao_score",
            trace_id=trace_log,
        )
    return ExplicacaoScoreLlmPersistidaSchema.model_validate(snapshot)


@router.get(
    "/{diagnostico_id}/explicacao-score-llm/historico",
    response_model=ExplicacaoScoreLlmHistoricoListaSchema,
    summary="Histórico de explicações LLM do score",
    description="Lista append-only das gerações anteriores (mais recente primeiro).",
)
async def listar_explicacao_score_llm_historico_painel(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    limit: int = 20,
) -> ExplicacaoScoreLlmHistoricoListaSchema:
    _, tenant_id, perfil_conta = current
    d = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    if not pode_gerar_explicacao_score_llm(perfil_conta, d):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=mensagem_acesso_negado_explicacao_score_llm(),
        )
    rows = await repo.listar_explicacao_score_llm_historico(diagnostico_id, tenant_id, limit=limit)
    items = [ExplicacaoScoreLlmPersistidaSchema.model_validate(r) for r in rows]
    return ExplicacaoScoreLlmHistoricoListaSchema(items=items)


@router.post(
    "/{diagnostico_id}/plano-acoes/{plano_acao_id}/subtarefas",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar subtarefa do plano materializado",
    description=(
        "Associa uma subtarefa a uma ação do plano (UUID ``plano_acao_id`` devolvido no GET). "
        "**Idempotency-Key** obrigatório (middleware de idempotência dos POST em ``/diagnosticos/``)."
    ),
)
async def criar_subtarefa_plano_diagnostico(
    diagnostico_id: UUID,
    plano_acao_id: UUID,
    payload: CriarSubtarefaPlanoDiagnosticoRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        CriarSubtarefaPlanoDiagnostico,
        Depends(get_criar_subtarefa_plano_diagnostico_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> DiagnosticoResponse:
    """POST subtarefa — exige diagnóstico finalizado com plano materializado."""
    _ = idempotency_key
    _, tenant_id, perfil_conta = current
    cmd = ComandoCriarSubtarefaPlanoDiagnostico(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        plano_acao_id=plano_acao_id,
        titulo=payload.titulo,
        ordem=payload.ordem,
    )
    try:
        await use_case.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    d = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    return await diagnostico_helpers._montar_diagnostico_response(
        repo, d, perfil_conta=perfil_conta
    )


@router.patch(
    "/{diagnostico_id}/plano-subtarefas/{subtarefa_id}",
    response_model=DiagnosticoResponse,
    summary="Atualizar subtarefa do plano materializado",
    description="Atualização parcial (título, status, prazo ISO, comentários, ordem).",
)
async def atualizar_subtarefa_plano_diagnostico(
    diagnostico_id: UUID,
    subtarefa_id: UUID,
    payload: PatchSubtarefaPlanoDiagnosticoRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarSubtarefaPlanoDiagnostico,
        Depends(get_atualizar_subtarefa_plano_diagnostico_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    _, tenant_id, perfil_conta = current
    cmd = ComandoAtualizarSubtarefaPlanoDiagnostico(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        subtarefa_id=subtarefa_id,
        titulo=payload.titulo,
        status=payload.status,
        prazo=payload.prazo,
        comentarios=payload.comentarios,
        ordem=payload.ordem,
    )
    try:
        await use_case.execute(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    d = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    return await diagnostico_helpers._montar_diagnostico_response(
        repo, d, perfil_conta=perfil_conta
    )


@router.patch("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def atualizar_relatorio_pdf(
    diagnostico_id: UUID,
    payload: PatchRelatorioPdfRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AnexarRelatorioOtimista,
        Depends(get_anexar_relatorio_otimista_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """
    Atualiza apenas `relatorio_pdf_url` em diagnóstico **finalizado**.

    Exige `If-Match` com a `versao_otimista` retornada no GET (lock otimista).
    """
    user_id, tenant_id, perfil_conta = current
    try:
        versao = diagnostico_helpers._parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAnexarRelatorioOtimista(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        relatorio_pdf_url=payload.relatorio_pdf_url,
        versao_esperada=versao,
        actor_user_id=user_id,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return await diagnostico_helpers._montar_diagnostico_response(
        repo, atualizado, perfil_conta=perfil_conta
    )
