"""
Rotas HTTP para o domínio de Diagnóstico.

Camada: Presentation
Responsabilidade: Roteamento HTTP, conversão Pydantic -> Domain.
"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.use_cases.anexar_relatorio_otimista import (
    AnexarRelatorioOtimista,
    ComandoAnexarRelatorioOtimista,
)
from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    RealizarDiagnostico,
)
from src.domain.entities.diagnostico import Diagnostico, EmpresaInfo, Respondente
from src.domain.entities.questionario import Pergunta, Resposta, TipoPergunta
from src.domain.value_objects.score import Dimensao, ScoreCompleto
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
)
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    IniciarDiagnosticoRequest,
    PatchRelatorioPdfRequest,
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
        raise ValueError(
            "Header If-Match obrigatório com a versão otimista atual (ex.: 1 ou \"1\")."
        )
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


def _montar_diagnostico_response(diagnostico: Diagnostico) -> DiagnosticoResponse:
    """Monta o payload HTTP canônico (checklist/matriz derivados do domínio)."""
    from dataclasses import asdict

    from src.application.services.consultoria_service import ConsultoriaService

    checklist_entities = ConsultoriaService.gerar_checklist(diagnostico)
    matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
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


def _get_banco_perguntas() -> list[Pergunta]:
    from uuid import UUID

    return [
        Pergunta(
            id=UUID("11111111-1111-4111-a111-111111111111"),
            codigo="Q-FISC-001",
            dimensao=Dimensao.FISCAL,
            texto="Sua empresa possui um departamento ou pessoa exclusivamente dedicada ao Compliance Tributário?",
            peso=1.5,
            tipo=TipoPergunta.ESCALA_1_5,
        ),
        Pergunta(
            id=UUID("22222222-2222-4222-a222-222222222222"),
            codigo="Q-TEC-001",
            dimensao=Dimensao.TECNOLOGICA,
            texto="Como é feita a apuração dos tributos hoje?",
            peso=1.3,
            tipo=TipoPergunta.ESCALA_1_5,
        ),
        Pergunta(
            id=UUID("33333333-3333-4333-a333-333333333333"),
            codigo="Q-EST-001",
            dimensao=Dimensao.ESTRATEGICA,
            texto="A empresa já iniciou o mapeamento dos impactos da EC 132/2023 (Reforma Tributária)?",
            peso=1.2,
            tipo=TipoPergunta.ESCALA_1_5,
        ),
    ]


@router.post("/", response_model=DiagnosticoResponse, status_code=status.HTTP_201_CREATED)
async def criar_diagnostico(
    payload: IniciarDiagnosticoRequest,
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
    )

    # 2. Match de Respostas com as Perguntas
    banco = _get_banco_perguntas()
    mapa_perguntas = {p.id: p for p in banco}

    respostas_domain = []
    perguntas_aplicadas = []

    for resp_payload in payload.respostas:
        pergunta = mapa_perguntas.get(resp_payload.pergunta_id)
        if not pergunta:
            raise HTTPException(
                status_code=400, detail=f"Pergunta não encontrada: {resp_payload.pergunta_id}"
            )

        # O diagnóstico ID real será instanciado dentro do UseCase,
        # mas a Resposta precisa de um. Vamos usar um dummy por enquanto ou o UseCase refatora.
        from uuid import uuid4

        respostas_domain.append(
            Resposta(
                diagnostico_id=uuid4(),  # Será ignorado pelo cálculo puro
                pergunta_id=pergunta.id,
                pergunta_tipo=pergunta.tipo,
                valor_bruto=resp_payload.valor,
            )
        )
        perguntas_aplicadas.append(pergunta)

    # 3. Montar Comando
    comando = ComandoRealizarDiagnostico(
        tenant_id=tenant_id,
        empresa=empresa_domain,
        respondente=respondente_domain,
        respostas=respostas_domain,
        perguntas_aplicadas=perguntas_aplicadas,
        plano=payload.plano,
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
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
    )


@router.get("/metodologia")
async def obter_metodologia() -> dict[str, Any]:
    """Retorna os pesos e a metodologia do motor de cálculo (Transparência)."""
    return {
        "versao_normativa": "ABNT NBR 17301:2026",
        "pesos_por_dimensao": {
            Dimensao.FISCAL.value: 1.5,
            Dimensao.ESTRATEGICA.value: 1.2,
            Dimensao.CONTABIL.value: 1.3,
            Dimensao.FINANCEIRA.value: 1.1,
            Dimensao.OPERACIONAL.value: 1.0,
            Dimensao.TECNOLOGICA.value: 1.4,
            Dimensao.COMPLIANCE_ABNT.value: 1.5,
        },
        "recomendacoes_gaps_criticos": [
            "Se o score Fiscal for < 40, recomenda-se auditoria imediata.",
            "Se o score Tecnológico for < 50, sugere-se adoção de ERP atualizado.",
        ],
    }


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
