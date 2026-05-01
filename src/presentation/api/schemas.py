"""
Schemas (DTOs) do Pydantic para validação HTTP.

Camada: Presentation
Responsabilidade:
    - Garantir que a API só receba payloads formatados corretamente.
    - Transformar objetos de Domínio puros em JSON limpo de saída.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.domain.entities.diagnostico import PorteEmpresa, RegimeTributario, SetorMacro

# =====================================================================
# Request Schemas (Entrada)
# =====================================================================


class RespondenteSchema(BaseModel):
    email: EmailStr
    nome: str | None = None
    cargo: str | None = None
    telefone: str | None = Field(
        default=None,
        max_length=32,
        description="Telefone opcional do respondente (M09 lead B2B; LGPD por finalidade).",
    )


class EmpresaSchema(BaseModel):
    cnpj: str = Field(
        ..., description="CNPJ com exatos 14 dígitos numéricos", min_length=14, max_length=14
    )
    razao_social: str
    porte: PorteEmpresa
    regime: RegimeTributario
    cnae_principal: str = Field(
        ..., description="CNAE principal com 7 dígitos", min_length=7, max_length=7
    )
    uf: str = Field(..., description="Sigla da UF com 2 letras", min_length=2, max_length=2)
    setor_macro: SetorMacro

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CNPJ deve conter apenas números")
        if len(v) != 14:
            raise ValueError("CNPJ deve conter exatos 14 dígitos")
        # Validação simplificada para o MVP. Em produção, incluir cálculo dos dígitos verificadores.
        if len(set(v)) == 1:
            raise ValueError("CNPJ não pode conter todos os dígitos iguais")
        return v

    @field_validator("uf")
    @classmethod
    def validar_uf(cls, v: str) -> str:
        ufs_validas = {
            "AC",
            "AL",
            "AP",
            "AM",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MT",
            "MS",
            "MG",
            "PA",
            "PB",
            "PR",
            "PE",
            "PI",
            "RJ",
            "RN",
            "RS",
            "RO",
            "RR",
            "SC",
            "SP",
            "SE",
            "TO",
        }
        v_upper = v.upper()
        if v_upper not in ufs_validas:
            raise ValueError(f"UF inválida: {v}")
        return v_upper


class RespostaRequestSchema(BaseModel):
    pergunta_id: UUID
    valor: (
        str | int | list[str]
    )  # ternária/binária: str; escala/número: int; múltipla/checklist: lista


class IniciarDiagnosticoRequest(BaseModel):
    empresa: EmpresaSchema
    respondente: RespondenteSchema
    respostas: list[RespostaRequestSchema]
    plano: str = "gratuito"


class PatchRelatorioPdfRequest(BaseModel):
    """Corpo do PATCH que só altera a URL do relatório (lock otimista via If-Match)."""

    relatorio_pdf_url: str = Field(..., min_length=1, max_length=4096)


class QuestionarioPerguntaItemSchema(BaseModel):
    """Item do catálogo filtrado pelo perfil (motor adaptativo)."""

    id: UUID
    codigo: str
    texto: str
    tipo: str
    peso: float
    dimensao: str
    base_legal: str | None = None
    multipla_total: int | None = None
    opcoes: list[str] | None = None


class QuestionarioDisponivelResponse(BaseModel):
    """Resposta do GET /diagnosticos/questionario."""

    versao_catalogo: str
    total: int
    perguntas: list[QuestionarioPerguntaItemSchema]


class ManifestoPesoPerguntaSchema(BaseModel):
    """Um item do catálogo com peso explícito (transparência M03)."""

    codigo: str
    dimensao: str
    tipo: str
    peso: float
    base_legal: str | None = None


class ManifestoPesosResponse(BaseModel):
    """
    Manifesto público — pesos por pergunta + pesos macro do score geral.

    LC 214/2025 art. 5º — previsibilidade; ABNT NBR 17301:2026 — transparência metodológica.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "versao_manifesto": "2026-04-30",
                "versao_catalogo": "v1-doc-05-full-37",
                "formula_score_geral": "Para cada dimensao: media ponderada...",
                "nota_calibracao_m02": "M02 - ...",
                "pesos_macro_dimensao": {"fiscal": 1.5, "tecnologica": 1.3},
                "perguntas": [
                    {
                        "codigo": "Q-EST-001",
                        "dimensao": "estrategica",
                        "tipo": "ternaria",
                        "peso": 7.5,
                        "base_legal": "EC 132/2023; LC 214/2025",
                    },
                ],
            }
        }
    )

    versao_manifesto: str = "2026-04-30"
    versao_catalogo: str
    formula_score_geral: str = (
        "Para cada dimensão: média ponderada das respostas pelo peso da pergunta. "
        "Score geral: média ponderada dos valores por dimensão usando pesos_macro_dimensao."
    )
    nota_calibracao_m02: str = (
        "M02 - Faixas de maturidade 0-100 e pesos sao deterministicos; calibracao "
        "fina por segmento apos coorte real (Beta)."
    )
    pesos_macro_dimensao: dict[str, float]
    perguntas: list[ManifestoPesoPerguntaSchema]


class ValidarAncoraNormativaRequest(BaseModel):
    """
    Texto livre para heurística MVP (plano ANALISE §E1).

    Aviso: validação léxica simples (`LC`, `NT`, referências tipo EC/ABNT) — não garante suficiência
    jurídica nem acoplamento Lexiq oficial (base RAG Tributiq).
    """

    texto: str = Field(..., min_length=1, max_length=50_000)


class ValidarAncoraNormativaResponse(BaseModel):
    """
    Saída heurística — apenas indica reconhecimento de padrões esperados pela API.

    Não usar como evidência jurídico-contábil autônoma (ABNT NBR 17301:2026: decisão segue ciclo corporativo formal).
    """

    valido: bool
    motivo_rejeicao: str | None = None


# =====================================================================
# Response Schemas (Saída)
# =====================================================================


class ScoreDimensaoSchema(BaseModel):
    valor: float
    peso_total_aplicado: float


class ScoreCompletoSchema(BaseModel):
    score_geral: ScoreDimensaoSchema
    score_por_dimensao: dict[str, ScoreDimensaoSchema]


class DiagnosticoResumoSchema(BaseModel):
    """Item resumido para listagem do tenant (P7 — dashboard B2B)."""

    id: UUID
    empresa_razao_social: str
    status: str
    plano: str
    score_geral: float | None = None
    criado_em: datetime
    finalizado_em: datetime | None = None
    relatorio_pdf_url: str | None = Field(
        default=None, description="URL do PDF quando gerado e anexado ao diagnóstico."
    )

    model_config = ConfigDict(from_attributes=True)


class DiagnosticoResponse(BaseModel):
    id: UUID
    status: str
    plano: str
    empresa_razao_social: str
    score: ScoreCompletoSchema | None = None
    relatorio_pdf_url: str | None = None
    recomendacao_ia: str | None = None
    checklist: list[dict[str, Any]] | None = None
    matriz_impacto: list[dict[str, Any]] | None = None
    cronograma: list[dict[str, Any]] | None = None
    # Trilha de auditoria (persistência: hash_sha256, versao_otimista — LC 214/2025, ABNT NBR 17301:2026)
    hash_evidencia: str | None = None
    versao_otimista: int | None = None

    model_config = ConfigDict(from_attributes=True)
