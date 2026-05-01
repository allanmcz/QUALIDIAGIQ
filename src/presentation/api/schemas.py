"""
Schemas (DTOs) do Pydantic para validação HTTP.

Camada: Presentation
Responsabilidade:
    - Garantir que a API só receba payloads formatados corretamente.
    - Transformar objetos de Domínio puros em JSON limpo de saída.
"""

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
    valor: str | int  # Ex: "sim", "nao", 1, 5


class IniciarDiagnosticoRequest(BaseModel):
    empresa: EmpresaSchema
    respondente: RespondenteSchema
    respostas: list[RespostaRequestSchema]
    plano: str = "gratuito"


class PatchRelatorioPdfRequest(BaseModel):
    """Corpo do PATCH que só altera a URL do relatório (lock otimista via If-Match)."""

    relatorio_pdf_url: str = Field(..., min_length=1, max_length=4096)


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
    plano: str
    empresa_razao_social: str
    score: ScoreCompletoSchema | None = None
    relatorio_pdf_url: str | None = None
    recomendacao_ia: str | None = None
    checklist: list[dict[str, Any]] | None = None
    matriz_impacto: list[dict[str, Any]] | None = None
    # Trilha de auditoria (persistência: hash_sha256, versao_otimista — LC 214/2025, ABNT NBR 17301:2026)
    hash_evidencia: str | None = None
    versao_otimista: int | None = None

    model_config = ConfigDict(from_attributes=True)
