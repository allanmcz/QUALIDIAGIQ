"""
Schemas (DTOs) do Pydantic para validação HTTP.

Camada: Presentation
Responsabilidade:
    - Garantir que a API só receba payloads formatados corretamente.
    - Transformar objetos de Domínio puros em JSON limpo de saída.
"""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.domain.entities.diagnostico import PorteEmpresa, RegimeTributario, SetorMacro

# =====================================================================
# Request Schemas (Entrada)
# =====================================================================


class RespondenteSchema(BaseModel):
    email: EmailStr
    nome: str | None = None
    cargo: str | None = None


class EmpresaSchema(BaseModel):
    cnpj: str = Field(..., description="CNPJ com exatos 14 dígitos", min_length=14, max_length=14)
    razao_social: str
    porte: PorteEmpresa
    regime: RegimeTributario
    cnae_principal: str = Field(..., description="CNAE principal", min_length=7)
    uf: str = Field(..., min_length=2, max_length=2)
    setor_macro: SetorMacro


class RespostaRequestSchema(BaseModel):
    pergunta_id: UUID
    valor: str | int  # Ex: "sim", "nao", 1, 5


class IniciarDiagnosticoRequest(BaseModel):
    empresa: EmpresaSchema
    respondente: RespondenteSchema
    respostas: list[RespostaRequestSchema]


# =====================================================================
# Response Schemas (Saída)
# =====================================================================


class ScoreDimensaoSchema(BaseModel):
    valor: float
    peso_total_aplicado: float


class ScoreCompletoSchema(BaseModel):
    score_geral: ScoreDimensaoSchema
    score_por_dimensao: dict[str, ScoreDimensaoSchema]


class DiagnosticoResponse(BaseModel):
    id: UUID
    status: str
    empresa_razao_social: str
    score: ScoreCompletoSchema | None = None
    relatorio_pdf_url: str | None = None

    model_config = ConfigDict(from_attributes=True)
