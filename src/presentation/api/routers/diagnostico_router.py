"""
Rotas HTTP para o domínio de Diagnóstico.

Camada: Presentation
Responsabilidade: Roteamento HTTP, conversão Pydantic -> Domain.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    RealizarDiagnostico,
)
from src.domain.entities.diagnostico import EmpresaInfo, Respondente
from src.domain.entities.questionario import Pergunta, Resposta, TipoPergunta
from src.domain.value_objects.score import Dimensao
from src.infrastructure.repositories.supabase_diagnostico_repository import (
    SupabaseDiagnosticoRepository,
)
from src.presentation.api.dependencies import (
    get_diagnostico_repository,
    get_realizar_diagnostico_use_case,
    get_tenant_id,
)
from src.presentation.api.schemas import (
    DiagnosticoResponse,
    IniciarDiagnosticoRequest,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


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
    tenant_id: Annotated[UUID, Depends(get_tenant_id)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    """Inicia um novo diagnóstico e calcula o score com base nas respostas."""

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
    )

    # 4. Executar Use Case
    try:
        resultado = await use_case.execute(comando)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

    return DiagnosticoResponse(
        id=resultado.diagnostico.id,
        status=resultado.diagnostico.status.value,
        empresa_razao_social=resultado.diagnostico.empresa.razao_social,
        score=score_completo_schema,
        relatorio_pdf_url=resultado.relatorio_pdf_url,
        recomendacao_ia=resultado.recomendacao_ia,
    )


@router.get("/metodologia")
async def obter_metodologia() -> dict:
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
            "Se o score Tecnológico for < 50, sugere-se adoção de ERP atualizado."
        ]
    }


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obter_diagnostico(
    diagnostico_id: UUID,
    tenant_id: Annotated[UUID, Depends(get_tenant_id)],
    repo: Annotated[SupabaseDiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Busca um diagnóstico pelo ID, garantindo o isolamento do tenant."""
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")

    # Obs: Como o Repositório do MVP (Supabase) ainda só salva score_geral numérico
    # e não o ScoreCompleto expandido, a serialização de GET devolverá o score parcial ou nulo.
    return DiagnosticoResponse(
        id=diagnostico.id,
        status=diagnostico.status.value,
        empresa_razao_social=diagnostico.empresa.razao_social,
        score=None,  # Para o MVP da Sprint 1 o GET retorna apenas metadados
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
        recomendacao_ia=None,
    )
