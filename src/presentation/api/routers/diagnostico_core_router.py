"""
Rotas HTTP core de Diagnóstico.

Camada: Presentation
Responsabilidade: CRUD principal autenticado do diagnóstico (listar, criar, obter).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003 - tipo usado em assinatura FastAPI (runtime)

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import Response

from src.application.errors import EliminacaoEmpresaSomenteWormError
from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.application.use_cases.arquivar_empresa_painel import (
    ArquivarEmpresaPainel,
    ComandoArquivarEmpresaPainel,
)
from src.application.use_cases.eliminar_diagnosticos_empresa_painel import (
    ComandoEliminarDiagnosticosEmpresaPainel,
    EliminarDiagnosticosEmpresaPainel,
)
from src.application.ports.empresa_painel_arquivo_port import EmpresaPainelArquivoPort
from src.application.use_cases.listar_retificacoes_diagnostico import (
    ComandoListarRetificacoesDiagnostico,
    ListarRetificacoesDiagnostico,
)
from src.application.use_cases.comparar_questionario_diagnosticos import (
    ComandoCompararQuestionario,
    CompararQuestionarioDiagnosticos,
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
    get_arquivar_empresa_painel_use_case,
    get_comparar_questionario_diagnosticos_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_eliminar_diagnosticos_empresa_painel_use_case,
    get_empresa_painel_arquivo_port,
    get_listar_retificacoes_diagnostico_use_case,
    get_pdf_generator,
    get_realizar_diagnostico_use_case,
    get_registrar_retificacao_diagnostico_use_case,
)
from src.infrastructure.adapters.pdf_generator_weasyprint import WeasyPrintPdfGenerator
from src.infrastructure.repositories.postgres_diagnostico_repository import (
    PostgresDiagnosticoRepository,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.routers import diagnostico_helpers
from src.presentation.api.schemas import (
    ComparacaoQuestionarioResponse,
    DiagnosticoQuestionarioRespostasResponse,
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    DiagnosticoRetificacaoHttpResponse,
    ArquivarEmpresaPainelHttpResponse,
    ArquivarEmpresaPainelRequest,
    EliminarEmpresaDiagnosticoHttpResponse,
    EmpresaArquivoStatusHttpResponse,
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
    arquivo_port: Annotated[EmpresaPainelArquivoPort, Depends(get_empresa_painel_arquivo_port)],
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
    incluir_arquivadas: Annotated[
        bool,
        Query(description="Se true, inclui empresas (CNPJ) arquivadas na listagem geral."),
    ] = False,
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
    excluir_arquivadas = filtro_cnpj is None and not incluir_arquivadas
    rows = await repo.listar_por_tenant(
        tenant_id,
        limit=limit,
        offset=offset,
        empresa_cnpj=filtro_cnpj,
        excluir_empresas_arquivadas=excluir_arquivadas,
    )
    if excluir_arquivadas and not isinstance(repo, PostgresDiagnosticoRepository):
        arquivados = await arquivo_port.listar_cnpjs_arquivados(tenant_id)
        rows = [
            d
            for d in rows
            if not d.empresa.cnpj or d.empresa.cnpj not in arquivados
        ]
    return [diagnostico_helpers._para_resumo(d) for d in rows]


@router.get(
    "/empresa/{empresa_cnpj}/arquivo",
    response_model=EmpresaArquivoStatusHttpResponse,
    summary="Estado de arquivo da empresa no painel",
)
async def status_arquivo_empresa_painel(
    empresa_cnpj: str,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    arquivo_port: Annotated[EmpresaPainelArquivoPort, Depends(get_empresa_painel_arquivo_port)],
) -> EmpresaArquivoStatusHttpResponse:
    _, tenant_id, _ = current
    norm = normalizar_cnpj_apenas_digitos(empresa_cnpj)
    try:
        exigir_cnpj_vazio_ou_com_dv_ok(norm)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    arquivado = await arquivo_port.esta_arquivada(tenant_id, norm)
    return EmpresaArquivoStatusHttpResponse(empresa_cnpj=norm, arquivado=arquivado)


@router.patch(
    "/empresa/{empresa_cnpj}/arquivo",
    response_model=ArquivarEmpresaPainelHttpResponse,
    summary="Arquivar ou restaurar empresa no painel",
    description=(
        "Oculta ou restaura a empresa (CNPJ) na listagem principal do painel. "
        "Não apaga diagnósticos finalizados (WORM). Exclusão de ciclos não finalizados "
        "permanece em DELETE /diagnosticos/empresa/{cnpj} dentro da vista da empresa."
    ),
)
async def arquivar_empresa_painel(
    empresa_cnpj: str,
    payload: ArquivarEmpresaPainelRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[ArquivarEmpresaPainel, Depends(get_arquivar_empresa_painel_use_case)],
) -> ArquivarEmpresaPainelHttpResponse:
    user_id, tenant_id, _ = current
    norm = normalizar_cnpj_apenas_digitos(empresa_cnpj)
    try:
        exigir_cnpj_vazio_ou_com_dv_ok(norm)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    resultado = await use_case.execute(
        ComandoArquivarEmpresaPainel(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            empresa_cnpj=norm,
            arquivado=payload.arquivado,
        )
    )
    if payload.arquivado:
        msg = (
            "Empresa arquivada no painel. Os diagnósticos permanecem acessíveis pelo link direto "
            "ou em «Ver empresas arquivadas»."
        )
        if not resultado.estado_alterado:
            msg = "Empresa já estava arquivada."
    else:
        msg = "Empresa restaurada na listagem do painel."
        if not resultado.estado_alterado:
            msg = "Empresa já estava visível no painel."
    return ArquivarEmpresaPainelHttpResponse(
        empresa_cnpj=resultado.empresa_cnpj,
        arquivado=resultado.arquivado,
        estado_alterado=resultado.estado_alterado,
        mensagem=msg,
    )


@router.delete(
    "/empresa/{empresa_cnpj}",
    response_model=EliminarEmpresaDiagnosticoHttpResponse,
    summary="Excluir ciclos não finalizados da empresa (CNPJ)",
    description=(
        "Remove fisicamente todos os diagnósticos do tenant com o CNPJ informado que ainda "
        "não estão ``finalizado`` (em andamento, cancelado ou expirado). "
        "Diagnósticos **finalizados** permanecem (WORM — ADR-012); use Privacidade LGPD por ciclo. "
        "Recomendado na vista da empresa, não na listagem geral. "
        "**Headers:** JWT + ``Idempotency-Key``."
    ),
)
async def eliminar_diagnosticos_empresa_painel(
    empresa_cnpj: str,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        EliminarDiagnosticosEmpresaPainel,
        Depends(get_eliminar_diagnosticos_empresa_painel_use_case),
    ],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> EliminarEmpresaDiagnosticoHttpResponse:
    """Limpeza operacional no painel — não substitui fluxo LGPD com solicitação deferida."""
    _ = idempotency_key
    user_id, tenant_id, _ = current
    norm = normalizar_cnpj_apenas_digitos(empresa_cnpj)
    try:
        exigir_cnpj_vazio_ou_com_dv_ok(norm)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    if len(norm) != 14:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CNPJ deve conter 14 dígitos com DV válido.",
        )
    try:
        resultado = await use_case.execute(
            ComandoEliminarDiagnosticosEmpresaPainel(
                tenant_id=tenant_id,
                actor_user_id=user_id,
                empresa_cnpj=norm,
            )
        )
    except EliminacaoEmpresaSomenteWormError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    msg = (
        f"{resultado.total_eliminados} diagnóstico(s) excluído(s) para o CNPJ informado."
    )
    if resultado.mantidos_finalizados > 0:
        msg += (
            f" {resultado.mantidos_finalizados} finalizado(s) mantido(s) "
            "(evidência WORM — use Privacidade LGPD se necessário)."
        )
    return EliminarEmpresaDiagnosticoHttpResponse(
        empresa_cnpj=resultado.empresa_cnpj,
        total_eliminados=resultado.total_eliminados,
        mantidos_finalizados=resultado.mantidos_finalizados,
        mantidos_outros_status=resultado.mantidos_outros_status,
        eliminados_ids=list(resultado.eliminados_ids),
        mensagem=msg,
    )


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


@router.get(
    "/comparar-questionario",
    response_model=ComparacaoQuestionarioResponse,
    summary="Comparar questionário entre diagnósticos",
    description=(
        "Alinha respostas por ``pergunta_codigo`` entre 2 e 5 diagnósticos da mesma empresa (mesmo tenant). "
        "Query ``ids``: UUIDs separados por vírgula."
    ),
)
async def comparar_questionario_diagnosticos(
    ids: Annotated[str, Query(description="UUIDs de diagnósticos separados por vírgula (2 a 5).")],
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        CompararQuestionarioDiagnosticos,
        Depends(get_comparar_questionario_diagnosticos_use_case),
    ],
) -> ComparacaoQuestionarioResponse:
    _, tenant_id, _ = current
    raw_ids = [p.strip() for p in ids.split(",") if p.strip()]
    try:
        uuid_ids = tuple(UUID(x) for x in raw_ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parâmetro ids contém UUID inválido.",
        ) from exc
    try:
        resultado = await use_case.execute(
            ComandoCompararQuestionario(tenant_id=tenant_id, diagnostico_ids=uuid_ids)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return ComparacaoQuestionarioResponse.model_validate(resultado)


@router.get(
    "/comparar-questionario/pdf",
    summary="PDF da comparação de questionários",
    description="Gera PDF WeasyPrint com a matriz de comparação (2 a 5 diagnósticos, mesmo CNPJ).",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def pdf_comparar_questionario(
    ids: Annotated[str, Query(description="UUIDs de diagnósticos separados por vírgula (2 a 5).")],
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        CompararQuestionarioDiagnosticos,
        Depends(get_comparar_questionario_diagnosticos_use_case),
    ],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(get_pdf_generator)],
) -> Response:
    _, tenant_id, _ = current
    raw_ids = [p.strip() for p in ids.split(",") if p.strip()]
    try:
        uuid_ids = tuple(UUID(x) for x in raw_ids)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Parâmetro ids contém UUID inválido.",
        ) from exc
    try:
        resultado = await use_case.execute(
            ComandoCompararQuestionario(tenant_id=tenant_id, diagnostico_ids=uuid_ids)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    ref = await repo.buscar_por_id(uuid_ids[0], tenant_id)
    if ref is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnóstico não encontrado")
    try:
        pdf_bytes = await pdf_generator.gerar_pdf_comparacao_questionario(
            resultado,
            contexto_diagnostico=ref,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    cnpj = str(resultado.get("empresa_cnpj", "") or uuid_ids[0].hex[:8]).replace("/", "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="qdi-comparacao-questionario-{cnpj}.pdf"',
        },
    )


@router.get(
    "/{diagnostico_id}/questionario-respostas/pdf",
    summary="PDF do questionário respondido",
    description="Gera PDF WeasyPrint com espelho pergunta/resposta (requer respostas materializadas).",
    responses={200: {"content": {"application/pdf": {}}}},
)
async def pdf_questionario_respostas(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    pdf_generator: Annotated[WeasyPrintPdfGenerator, Depends(get_pdf_generator)],
) -> Response:
    _, tenant_id, _ = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnóstico não encontrado")
    respostas = await repo.listar_respostas_questionario(diagnostico_id, tenant_id)
    if not respostas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Este diagnóstico não possui respostas materializadas "
                "(ciclos anteriores à versão com questionário persistido)."
            ),
        )
    try:
        pdf_bytes = await pdf_generator.gerar_pdf_questionario_respostas(diagnostico, respostas)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)) from e
    nome = (diagnostico.empresa.cnpj or str(diagnostico_id)[:8]).replace("/", "")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="qdi-questionario-{nome}.pdf"',
        },
    )


@router.get(
    "/{diagnostico_id}/questionario-respostas",
    response_model=DiagnosticoQuestionarioRespostasResponse,
    summary="Listar respostas do questionário",
    description=(
        "Snapshot imutável das respostas por pergunta (tabela normalizada). "
        "Permite comparar ciclos da mesma empresa via ``pergunta_codigo`` e evolução no painel."
    ),
)
async def listar_questionario_respostas(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoQuestionarioRespostasResponse:
    """Lista respostas materializadas na finalização do diagnóstico."""
    _, tenant_id, _ = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnóstico não encontrado")
    itens = await repo.listar_respostas_questionario(diagnostico_id, tenant_id)
    return DiagnosticoQuestionarioRespostasResponse(
        diagnostico_id=diagnostico_id,
        total=len(itens),
        respostas=itens,
    )


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obter_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Busca um diagnóstico pelo ID, garantindo o isolamento do tenant."""
    _, tenant_id, perfil_conta = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")
    return await diagnostico_helpers._montar_diagnostico_response(
        repo, diagnostico, perfil_conta=perfil_conta
    )
