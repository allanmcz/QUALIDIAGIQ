"""
Rotas HTTP públicas de Diagnóstico (transparência normativa e questionário adaptativo).

Camada: Presentation
Responsabilidade: endpoints sem JWT — metodologia, manifesto de pesos e catálogo filtrado.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.domain.entities.diagnostico import EmpresaInfo
from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente
from src.domain.value_objects.score import PesoMacroNormativoVigente
from src.infrastructure.questionario.banco_cache import (
    get_catalogo_perguntas_efetivo,
    versao_catalogo_lida,
)
from src.presentation.api.dependencies import (
    PesosMacroPublicacaoHttp,
    get_gerar_questionario_adaptativo_use_case,
    perfil_empresa_para_questionario,
    pesos_macro_publicacao_para_http,
)
from src.presentation.api.schemas import (
    ManifestoPesoPerguntaSchema,
    ManifestoPesosResponse,
    MetodologiaResponse,
    NormativaPesoPerguntaOverlaySchema,
    PesoMacroNormativaItemSchema,
    QuestionarioDisponivelResponse,
    QuestionarioPerguntaItemSchema,
)

router = APIRouter()


def _pesos_macro_normativa_para_schema(
    metadados: dict[str, PesoMacroNormativoVigente],
) -> dict[str, PesoMacroNormativaItemSchema]:
    """Converte value objects de domínio em DTOs HTTP (evita import cruzado deps → schemas)."""
    return {
        k: PesoMacroNormativaItemSchema(
            peso=float(v.peso),
            vigencia_inicio=v.vigencia_inicio,
            vigencia_fim=v.vigencia_fim,
            rotulo_versao=v.rotulo_versao,
        )
        for k, v in metadados.items()
    }


def _peso_pergunta_overlay_para_schema(
    peso_catalogo_json: float,
    meta: PesoPerguntaNormativoVigente,
) -> NormativaPesoPerguntaOverlaySchema:
    """Converte VO de domínio em DTO HTTP (manifesto público)."""
    return NormativaPesoPerguntaOverlaySchema(
        peso_catalogo_json=float(peso_catalogo_json),
        peso_normativo_db=float(meta.peso),
        vigencia_inicio=meta.vigencia_inicio,
        vigencia_fim=meta.vigencia_fim,
        rotulo_versao=meta.rotulo_versao,
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
async def obter_metodologia(
    macro_pub: Annotated[PesosMacroPublicacaoHttp, Depends(pesos_macro_publicacao_para_http)],
) -> MetodologiaResponse:
    """Retorna os pesos macro e a metodologia do motor de cálculo (transparência M03)."""
    return MetodologiaResponse(
        versao_normativa="ABNT NBR 17301:2026",
        pesos_macro_dimensao_score_geral=macro_pub.valores,
        pesos_macro_dimensao_normativa=_pesos_macro_normativa_para_schema(
            macro_pub.metadados_por_dimensao
        ),
        nota_metodologica=(
            "O QualiDiagIQ produz um índice único de 0 a 100 — maturidade tributária frente à Reforma "
            "do Consumo (EC 132/2023, LC 214/2025), com âncora metodológica na ABNT NBR 17301:2026. "
            "Para cada dimensão avaliada, calculamos um resultado a partir das suas respostas ao "
            "questionário, usando os pesos individuais do catálogo (totalmente públicos no manifesto "
            "de perguntas). Em seguida, combinamos esses resultados dimensionais com pesos estratégicos "
            "macro — por exemplo, maior peso na dimensão fiscal, por concentrar exposição normativa e "
            "operacional na transição para CBS/IBS. O mesmo critério é aplicado a todos os diagnósticos "
            "na mesma versão do produto, permitindo comparabilidade e auditoria."
        ),
        recomendacoes_gaps_criticos=[
            "Dimensão fiscal com resultado baixo: priorize revisão de cadastros tributários, "
            "classificações e cenários CBS/IBS com apoio contábil ou consultoria especializada — "
            "pistas de trabalho, não substituem parecer jurídico.",
            "Dimensão tecnológica com resultado baixo: avalie integração entre ERP e registros fiscais "
            "e a robustez dos dados para sustentar o novo arcaboço — frequentemente gargalo em projetos "
            "de adequação.",
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
async def obter_manifesto_pesos(
    macro_pub: Annotated[PesosMacroPublicacaoHttp, Depends(pesos_macro_publicacao_para_http)],
) -> ManifestoPesosResponse:
    """
    Manifesto público de pesos (M03) — catálogo completo + macrodimensões do score geral.

    Endpoint público (sem JWT), coerente com transparência do motor.
    """
    ce = get_catalogo_perguntas_efetivo()
    overlays = ce.overlay_por_codigo
    itens: list[ManifestoPesoPerguntaSchema] = []
    for p in ce.perguntas:
        ov_raw = overlays.get(p.codigo)
        overlay_schema = (
            _peso_pergunta_overlay_para_schema(ov_raw[0], ov_raw[1]) if ov_raw is not None else None
        )
        itens.append(
            ManifestoPesoPerguntaSchema(
                codigo=p.codigo,
                dimensao=p.dimensao.value,
                tipo=p.tipo.value,
                peso=p.peso,
                base_legal=p.base_legal,
                pilar_abnt=p.pilar_abnt,
                normativa_overlay=overlay_schema,
            )
        )
    return ManifestoPesosResponse(
        versao_catalogo=versao_catalogo_lida(),
        pesos_macro_dimensao=macro_pub.valores,
        pesos_macro_dimensao_normativa=_pesos_macro_normativa_para_schema(
            macro_pub.metadados_por_dimensao
        ),
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
            rotulos_escala=list(p.rotulos_escala) if p.rotulos_escala else None,
            pilar_abnt=p.pilar_abnt,
        )
        for p in lista
    ]
    return QuestionarioDisponivelResponse(
        versao_catalogo=versao_catalogo_lida(),
        total=len(itens),
        perguntas=itens,
    )
