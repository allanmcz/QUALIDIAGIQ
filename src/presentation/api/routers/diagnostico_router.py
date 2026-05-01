"""
Rotas HTTP para o domínio de Diagnóstico.

Camada: Presentation
Responsabilidade: Roteamento HTTP, conversão Pydantic -> Domain.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.use_cases.anexar_relatorio_otimista import (
    AnexarRelatorioOtimista,
    ComandoAnexarRelatorioOtimista,
)
from src.application.use_cases.atualizar_checklist_m12_autoconf import (
    AtualizarChecklistM12Autoconf,
    ComandoAtualizarChecklistM12Autoconf,
)
from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    EntradaRespostaDiagnostico,
    RealizarDiagnostico,
)
from src.domain.entities.diagnostico import Diagnostico, EmpresaInfo, Respondente
from src.domain.value_objects.score import ScoreCompleto, pesos_macro_dimensao_para_dict_iso
from src.infrastructure.questionario.banco_cache import (
    get_banco_perguntas_cached,
    versao_catalogo_lida,
)
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_atualizar_checklist_m12_autoconf_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_gerar_questionario_adaptativo_use_case,
    get_realizar_diagnostico_use_case,
    perfil_empresa_para_questionario,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    IniciarDiagnosticoRequest,
    ManifestoPesoPerguntaSchema,
    ManifestoPesosResponse,
    MetodologiaResponse,
    PatchChecklistM12AutoconfRequest,
    PatchRelatorioPdfRequest,
    QuestionarioDisponivelResponse,
    QuestionarioPerguntaItemSchema,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


def _campos_auditoria_http(entity: object) -> tuple[str | None, int | None]:
    """Extrai hash/versão apenas se tipos forem válidos (evita MagicMock nos testes unitários)."""
    raw_h = getattr(entity, "hash_evidencia", None)
    hash_out: str | None = raw_h if isinstance(raw_h, str) else None
    raw_v = getattr(entity, "versao_otimista", None)
    versao_out: int | None = raw_v if isinstance(raw_v, int) else None
    return hash_out, versao_out


def _parse_if_match_versao(raw: str | None) -> int:
    """
    Interpreta If-Match como inteiro (versao_otimista).

    Aceita formas comuns: `3`, `"3"`, `W/"3"` (usa apenas o primeiro valor se houver lista).
    """
    if raw is None or not str(raw).strip():
        raise ValueError('Header If-Match obrigatório com a versão otimista atual (ex.: 1 ou "1").')
    s = str(raw).strip()
    if "," in s:
        s = s.split(",", 1)[0].strip()
    if s.upper().startswith("W/"):
        s = s[2:].strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    try:
        v = int(s)
    except ValueError as e:
        raise ValueError("If-Match deve ser um inteiro (versão otimista).") from e
    if v < 1:
        raise ValueError("Versão otimista inválida.")
    return v


def _checklist_m12_para_http(diagnostico: Diagnostico) -> list[bool] | None:
    """Extrai lista persistida para o contrato HTTP (evita `MagicMock` nos testes)."""
    raw = getattr(diagnostico, "checklist_m12_estado", None)
    if not isinstance(raw, list) or len(raw) != 10:
        return None
    if not all(isinstance(x, bool) for x in raw):
        return None
    return list(raw)


def _aceite_lgpd_para_http(diagnostico: Diagnostico) -> datetime | None:
    """Instante do aceite LGPD persistido (somente `datetime` real)."""
    raw = getattr(diagnostico, "aceite_termos_privacidade_em", None)
    return raw if isinstance(raw, datetime) else None


def _para_resumo(diagnostico: Diagnostico) -> DiagnosticoResumoSchema:
    """Monta linha da listagem B2B (P7 — sem recomputar checklist/matriz)."""
    return DiagnosticoResumoSchema(
        id=diagnostico.id,
        empresa_razao_social=diagnostico.empresa.razao_social,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        score_geral=diagnostico.score_geral,
        criado_em=diagnostico.criado_em,
        finalizado_em=diagnostico.finalizado_em,
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
    )


def _montar_diagnostico_response(diagnostico: Diagnostico) -> DiagnosticoResponse:
    """Monta o payload HTTP canônico (checklist/matriz derivados do domínio)."""
    from dataclasses import asdict

    from src.application.services.consultoria_service import ConsultoriaService

    snap_chk = getattr(diagnostico, "score_completo_snapshot", None)
    checklist_entities = ConsultoriaService.gerar_checklist(
        diagnostico,
        snap_chk if isinstance(snap_chk, ScoreCompleto) else None,
    )
    matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
    cronograma_data = ConsultoriaService.gerar_cronograma_cinco_fases()
    checklist_data = [asdict(f) for f in checklist_entities]
    matriz_data = [asdict(m) for m in matriz_entities]
    h_aud, v_aud = _campos_auditoria_http(diagnostico)
    return DiagnosticoResponse(
        id=diagnostico.id,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        empresa_razao_social=diagnostico.empresa.razao_social,
        score=_score_completo_para_http(diagnostico),
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
        recomendacao_ia=None,
        checklist=checklist_data,
        matriz_impacto=matriz_data,
        cronograma=cronograma_data,
        checklist_m12_autoconf=_checklist_m12_para_http(diagnostico),
        aceite_termos_privacidade_em=_aceite_lgpd_para_http(diagnostico),
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
    )


def _score_completo_para_http(diagnostico: Diagnostico) -> ScoreCompletoSchema | None:
    """Monta o schema HTTP a partir do snapshot persistido (JSONB), se existir."""
    snap = getattr(diagnostico, "score_completo_snapshot", None)
    if snap is None or not isinstance(snap, ScoreCompleto):
        return None
    return ScoreCompletoSchema(
        score_geral=ScoreDimensaoSchema(
            valor=snap.score_geral.valor,
            peso_total_aplicado=snap.score_geral.peso_total_aplicado,
        ),
        score_por_dimensao={
            dim.value: ScoreDimensaoSchema(
                valor=sn.valor, peso_total_aplicado=sn.peso_total_aplicado
            )
            for dim, sn in snap.score_por_dimensao.items()
        },
    )


@router.get("/", response_model=list[DiagnosticoResumoSchema])
async def listar_diagnosticos(
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DiagnosticoResumoSchema]:
    """Lista diagnósticos do tenant atual (ordenacao: mais recentes primeiro na camada repo/DB)."""
    _, tenant_id = current
    rows = await repo.listar_por_tenant(tenant_id, limit=limit, offset=offset)
    return [_para_resumo(d) for d in rows]


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
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    """Inicia um novo diagnóstico e calcula o score com base nas respostas."""
    _, tenant_id = current

    # 1. Converter Schemas Pydantic para Entidades de Domínio
    empresa_domain = EmpresaInfo(
        cnpj=payload.empresa.cnpj,
        razao_social=payload.empresa.razao_social,
        porte=payload.empresa.porte,
        regime=payload.empresa.regime,
        cnae_principal=payload.empresa.cnae_principal,
        uf=payload.empresa.uf,
        setor_macro=payload.empresa.setor_macro,
    )

    respondente_domain = Respondente(
        email=payload.respondente.email,
        nome=payload.respondente.nome,
        cargo=payload.respondente.cargo,
        telefone=payload.respondente.telefone,
    )

    # 2. Match de Respostas com as Perguntas
    banco = get_banco_perguntas_cached()
    mapa_perguntas = {p.id: p for p in banco}

    entradas_resposta: list[EntradaRespostaDiagnostico] = []
    for resp_payload in payload.respostas:
        pergunta = mapa_perguntas.get(resp_payload.pergunta_id)
        if not pergunta:
            raise HTTPException(
                status_code=400, detail=f"Pergunta não encontrada: {resp_payload.pergunta_id}"
            )
        entradas_resposta.append(
            EntradaRespostaDiagnostico(pergunta=pergunta, valor_bruto=resp_payload.valor)
        )

    # 3. Montar comando (UUID do diagnóstico aplicado apenas no use case, sobre entidade criada lá)
    comando = ComandoRealizarDiagnostico(
        tenant_id=tenant_id,
        empresa=empresa_domain,
        respondente=respondente_domain,
        entradas_resposta=entradas_resposta,
        plano=payload.plano,
        aceite_termos_privacidade=payload.aceite_termos_privacidade,
    )

    # 4. Executar Use Case
    try:
        resultado = await use_case.execute(comando)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # 5. Mapear Resposta de volta para Schema Pydantic
    score_por_dimensao_schema = {
        dim.value: ScoreDimensaoSchema(valor=sn.valor, peso_total_aplicado=sn.peso_total_aplicado)
        for dim, sn in resultado.score.score_por_dimensao.items()
    }

    score_completo_schema = ScoreCompletoSchema(
        score_geral=ScoreDimensaoSchema(
            valor=resultado.score.score_geral.valor,
            peso_total_aplicado=resultado.score.score_geral.peso_total_aplicado,
        ),
        score_por_dimensao=score_por_dimensao_schema,
    )

    d = resultado.diagnostico
    h_aud, v_aud = _campos_auditoria_http(d)
    return DiagnosticoResponse(
        id=d.id,
        status=d.status.value,
        plano=d.plano.value,
        empresa_razao_social=d.empresa.razao_social,
        score=score_completo_schema,
        relatorio_pdf_url=resultado.relatorio_pdf_url,
        recomendacao_ia=resultado.recomendacao_ia,
        checklist=resultado.checklist,
        matriz_impacto=resultado.matriz_impacto,
        cronograma=resultado.cronograma,
        checklist_m12_autoconf=_checklist_m12_para_http(d),
        aceite_termos_privacidade_em=_aceite_lgpd_para_http(d),
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
    )


@router.get(
    "/metodologia",
    response_model=MetodologiaResponse,
    summary="Metodologia e pesos macro do score geral",
    description=(
        "Endpoint **público** (sem JWT). Expõe `pesos_macro_dimensao_score_geral` usados na "
        "agregação do score 0-100 e texto metodológico. Detalhamento por pergunta: "
        "**GET /diagnosticos/manifesto-pesos**."
    ),
)
async def obter_metodologia() -> MetodologiaResponse:
    """Retorna os pesos macro e a metodologia do motor de cálculo (transparência M03)."""
    return MetodologiaResponse(
        versao_normativa="ABNT NBR 17301:2026",
        pesos_macro_dimensao_score_geral=pesos_macro_dimensao_para_dict_iso(),
        nota_metodologica=(
            "pesos_macro_dimensao_score_geral ponderam apenas a agregação do score "
            "a partir das médias por dimensão; dentro de cada dimensão usam-se os pesos "
            "do catálogo (ver GET /diagnosticos/manifesto-pesos)."
        ),
        recomendacoes_gaps_criticos=[
            "Se o score Fiscal for < 40, recomenda-se auditoria imediata.",
            "Se o score Tecnológico for < 50, sugere-se adoção de ERP atualizado.",
        ],
    )


@router.get(
    "/manifesto-pesos",
    response_model=ManifestoPesosResponse,
    summary="Manifesto público de pesos por pergunta",
    description=(
        "Catálogo completo com peso e dimensão por código de pergunta; inclui `versao_catalogo` "
        "e `pesos_macro_dimensao` aplicados ao score geral. **Público**, sem JWT — auditable "
        "(LC 214/2025, ABNT NBR 17301:2026)."
    ),
)
async def obter_manifesto_pesos() -> ManifestoPesosResponse:
    """
    Manifesto público de pesos (M03) — catálogo completo + macrodimensões do score geral.

    Endpoint público (sem JWT), coerente com transparência do motor.
    """
    banco = get_banco_perguntas_cached()
    itens = [
        ManifestoPesoPerguntaSchema(
            codigo=p.codigo,
            dimensao=p.dimensao.value,
            tipo=p.tipo.value,
            peso=p.peso,
            base_legal=p.base_legal,
        )
        for p in banco
    ]
    return ManifestoPesosResponse(
        versao_catalogo=versao_catalogo_lida(),
        pesos_macro_dimensao=pesos_macro_dimensao_para_dict_iso(),
        perguntas=itens,
    )


@router.get("/questionario", response_model=QuestionarioDisponivelResponse)
async def obter_questionario_adaptativo(
    empresa: Annotated[EmpresaInfo, Depends(perfil_empresa_para_questionario)],
    use_case: Annotated[
        GerarQuestionarioAdaptativoUseCase,
        Depends(get_gerar_questionario_adaptativo_use_case),
    ],
) -> QuestionarioDisponivelResponse:
    """
    Lista perguntas aplicáveis ao perfil declarado (motor adaptativo).

    Endpoint **público** (sem JWT): catálogo filtrado não expõe dados de tenant.
    POST `/diagnosticos/` continua exigindo Bearer + Idempotency-Key.

    LC 214/2025 — transparência e previsibilidade na coleta de informações do contribuinte.
    """
    try:
        lista = use_case.execute(empresa)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    itens = [
        QuestionarioPerguntaItemSchema(
            id=p.id,
            codigo=p.codigo,
            texto=p.texto,
            tipo=p.tipo.value,
            peso=p.peso,
            dimensao=p.dimensao.value,
            base_legal=p.base_legal,
            multipla_total=p.multipla_total,
            opcoes=list(p.opcoes) if p.opcoes else None,
        )
        for p in lista
    ]
    return QuestionarioDisponivelResponse(
        versao_catalogo=versao_catalogo_lida(),
        total=len(itens),
        perguntas=itens,
    )


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obter_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Busca um diagnóstico pelo ID, garantindo o isolamento do tenant."""
    _, tenant_id = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")

    return _montar_diagnostico_response(diagnostico)


@router.patch(
    "/{diagnostico_id}/checklist-m12-autoconf",
    response_model=DiagnosticoResponse,
    summary="Atualizar autoconf ABNT M12",
    description=(
        "Persiste os 10 booleanos da autoconferência (ABNT NBR 17301). "
        "Exige diagnóstico **finalizado** e header **If-Match** com `versao_otimista` atual."
    ),
)
async def atualizar_checklist_m12_autoconf(
    diagnostico_id: UUID,
    payload: PatchChecklistM12AutoconfRequest,
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarChecklistM12Autoconf,
        Depends(get_atualizar_checklist_m12_autoconf_use_case),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """PATCH M12 — lock otimista alinhado ao PATCH de relatório PDF."""
    _, tenant_id = current
    try:
        versao = _parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        checklist_m12_autoconf=list(payload.checklist_m12_autoconf),
        versao_esperada=versao,
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

    return _montar_diagnostico_response(atualizado)


@router.patch("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def atualizar_relatorio_pdf(
    diagnostico_id: UUID,
    payload: PatchRelatorioPdfRequest,
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AnexarRelatorioOtimista,
        Depends(get_anexar_relatorio_otimista_use_case),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """
    Atualiza apenas `relatorio_pdf_url` em diagnóstico **finalizado**.

    Exige `If-Match` com a `versao_otimista` retornada no GET (lock otimista).
    """
    _, tenant_id = current
    try:
        versao = _parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAnexarRelatorioOtimista(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        relatorio_pdf_url=payload.relatorio_pdf_url,
        versao_esperada=versao,
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

    return _montar_diagnostico_response(atualizado)
