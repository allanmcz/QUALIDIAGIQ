"""
Schemas (DTOs) do Pydantic para validação HTTP.

Camada: Presentation
Responsabilidade:
    - Garantir que a API só receba payloads formatados corretamente.
    - Transformar objetos de Domínio puros em JSON limpo de saída.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.domain.entities.diagnostico import (
    FaixaFaturamentoDeclarada,
    PorteEmpresa,
    RegimeTributario,
    SetorMacro,
)
from src.domain.value_objects.cnpj_brasil import (
    cnpj_com_digitos_verificadores_validos,
    normalizar_cnpj_apenas_digitos,
)

# =====================================================================
# Request Schemas (Entrada)
# =====================================================================


class RespondenteSchema(BaseModel):
    """Respondente do diagnóstico — e-mail e nome obrigatórios (vínculo LGPD / rastreio)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    nome: str = Field(
        min_length=1,
        max_length=255,
        description="Nome do respondente que vincula o diagnóstico ao contato (obrigatório).",
    )
    cargo: str | None = None
    telefone: str | None = Field(
        default=None,
        max_length=15,
        description=(
            "Telefone opcional, apenas dígitos: DDD + número (10 ou 11 dígitos), sem DDI (+55). "
            "M09 lead B2B; LGPD por finalidade."
        ),
    )

    @field_validator("telefone", mode="before")
    @classmethod
    def normalizar_telefone_br_sem_ddi(cls, v: object) -> str | None:
        """Remove máscara e valida comprimento típico BR (fixo ou celular)."""
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        digitos = "".join(c for c in str(v) if c.isdigit())
        if len(digitos) == 0:
            return None
        if len(digitos) not in (10, 11):
            raise ValueError("Telefone sem DDI: informe DDD + número (10 ou 11 dígitos).")
        return digitos


class EmpresaSchema(BaseModel):
    cnpj: str = Field(
        ...,
        max_length=18,
        description=(
            "CNPJ: 14 dígitos numéricos ou com máscara (00.000.000/0000-00). Obrigatório no POST "
            "de diagnóstico — cadastro da empresa (vínculo PJ) junto à razão social. "
            "Após validação, armazenado sem máscara."
        ),
    )
    razao_social: str
    porte: PorteEmpresa
    regime: RegimeTributario
    cnae_principal: str = Field(
        ..., description="CNAE principal com 7 dígitos", min_length=7, max_length=7
    )
    uf: str = Field(..., description="Sigla da UF com 2 letras", min_length=2, max_length=2)
    setor_macro: SetorMacro
    faixa_faturamento: FaixaFaturamentoDeclarada | None = Field(
        default=None,
        description=(
            "Opcional — faixa de faturamento bruto anual autodeclarada (R$), para segmentação; "
            "omitir ou null se o respondente não informar."
        ),
    )

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        raw = normalizar_cnpj_apenas_digitos(v or "")
        if raw == "":
            raise ValueError("CNPJ é obrigatório no cadastro da empresa para o diagnóstico.")
        if len(raw) != 14:
            raise ValueError("CNPJ deve conter exatos 14 dígitos numéricos")
        if len(set(raw)) == 1:
            raise ValueError("CNPJ não pode conter todos os dígitos iguais")
        if not cnpj_com_digitos_verificadores_validos(raw):
            raise ValueError("CNPJ inválido: dígitos verificadores não conferem")
        return raw

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
    locale_relatorio: Literal["pt-BR", "en"] = Field(
        default="pt-BR",
        description=(
            "Idioma do relatório PDF (WeasyPrint): pt-BR completo; en — labels em inglês "
            "(conteúdo gerado dinamicamente pode permanecer em PT até tradução total)."
        ),
    )
    aceite_termos_privacidade: bool = Field(
        ...,
        description=(
            "Ciência explícita dos termos de uso e desta política de privacidade (LGPD Lei 13.709/2018)."
        ),
    )

    @field_validator("aceite_termos_privacidade")
    @classmethod
    def aceite_obrigatorio_true(cls, v: bool) -> bool:
        """Somente `true` aceita — coerente com o checkbox obrigatório do wizard."""
        if v is not True:
            raise ValueError(
                "É obrigatório aceitar o tratamento dos dados conforme a política de privacidade."
            )
        return v


class PatchRelatorioPdfRequest(BaseModel):
    """Corpo do PATCH que só altera a URL do relatório (lock otimista via If-Match)."""

    relatorio_pdf_url: str = Field(..., min_length=1, max_length=4096)


class PatchChecklistM12AutoconfRequest(BaseModel):
    """
    Corpo do PATCH M12 — espelho dos 10 controles ABNT (booleanos).

    Exige `If-Match` com `versao_otimista` atual (mesmo contrato do PATCH de relatório).
    """

    checklist_m12_autoconf: list[bool] = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Exatamente 10 valores — mesma ordem das ações da frente ABNT no relatório.",
    )


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
    rotulos_escala: list[str] | None = Field(
        default=None,
        description=(
            "Somente escala_1_5: exatamente 5 rótulos para valores 1 a 5 (catálogo); "
            "se omitido, o cliente aplica rótulos padrão de maturidade."
        ),
    )
    pilar_abnt: str | None = Field(
        default=None,
        description="Referência opcional ao pilar/tema ABNT NBR 17301:2026 vinculado à pergunta.",
    )


class QuestionarioDisponivelResponse(BaseModel):
    """Resposta do GET /diagnosticos/questionario."""

    versao_catalogo: str
    total: int
    perguntas: list[QuestionarioPerguntaItemSchema]


class ManifestoPesoPerguntaSchema(BaseModel):
    """Um item do catálogo com peso explícito (transparência M03)."""

    codigo: str = Field(..., description="Código canônico da pergunta (ex.: Q-EST-001).")
    dimensao: str = Field(
        ...,
        description="Dimensão ABNT / score (fiscal, estrategica, tecnologica, etc.).",
    )
    tipo: str = Field(..., description="Tipo de resposta (ternaria, binaria, escala_1_5, ...).")
    peso: float = Field(..., description="Peso no cálculo dentro da dimensão.")
    base_legal: str | None = Field(
        default=None,
        description="Referência normativa associada à pergunta (LC 214/2025, NT, EC 132/2023, ...).",
    )
    pilar_abnt: str | None = Field(
        default=None,
        description="Pilar/tema ABNT NBR 17301:2026 opcional (catálogo versionado).",
    )


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
                "formula_score_geral": (
                    "Em cada dimensão, média ponderada das respostas; score geral: agregação ponderada."
                ),
                "nota_calibracao_m02": (
                    "Pesos e faixas determinísticos; versão do manifesto identifica o critério aplicado."
                ),
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
        "Em cada dimensão (Fiscal, Estratégica, Contábil, Financeira, Operacional, Tecnológica e "
        "Compliance ABNT NBR 17301), calculamos uma média ponderada das respostas aplicáveis ao seu "
        "perfil, usando o peso de cada pergunta do catálogo. O score geral (0 a 100) é a média "
        "ponderada desses resultados dimensionais, segundo os pesos macro publicados nesta página — "
        "critério único e auditável para todos os diagnósticos na mesma versão do produto."
    )
    nota_calibracao_m02: str = (
        "As faixas de maturidade e os pesos são definidos de forma determinística e documentada, "
        "garantindo repetibilidade entre execuções. Evoluções por segmento ou porte podem ser "
        "incorporadas em versões futuras do manifesto, sempre com identificação de versão — sua "
        "organização sabe exatamente qual critério fundamentou o relatório recebido."
    )
    pesos_macro_dimensao: dict[str, float]
    perguntas: list[ManifestoPesoPerguntaSchema]


class MetodologiaResponse(BaseModel):
    """
    Conteúdo de GET /diagnosticos/metodologia — alinhamento do motor com transparência (M03).

    Público, sem JWT. Complementa o manifesto de pesos.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "versao_normativa": "ABNT NBR 17301:2026",
                "pesos_macro_dimensao_score_geral": {
                    "fiscal": 1.5,
                    "estrategica": 1.0,
                    "tecnologica": 1.3,
                },
                "nota_metodologica": (
                    "Índice 0 a 100 por dimensões; agregação com pesos macro; catálogo público de perguntas."
                ),
                "recomendacoes_gaps_criticos": [
                    "Dimensão fiscal baixa: revisar cadastros e cenários CBS/IBS com apoio especializado.",
                ],
            }
        }
    )

    versao_normativa: str = Field(
        ...,
        description="Referência de norma-guia usada na camada de compliance (ex.: ABNT NBR 17301:2026).",
    )
    pesos_macro_dimensao_score_geral: dict[str, float] = Field(
        ...,
        description="Pesos que agregam as médias por dimensão no score geral 0-100 (ver domain).",
    )
    nota_metodologica: str = Field(
        ...,
        description="Texto explicando a relação entre pesos macro e pesos do catálogo por pergunta.",
    )
    recomendacoes_gaps_criticos: list[str] = Field(
        default_factory=list,
        description="Alertas heurísticos para leitura executiva (não vinculam obrigação legal).",
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "valido": True,
                "motivo_rejeicao": None,
            },
        }
    )

    valido: bool = Field(..., description="True se o texto contém padrão de âncora normativa MVP.")
    motivo_rejeicao: str | None = Field(
        default=None,
        description="Preenchido quando valido=false (mensagem para UX / wizard).",
    )


# =====================================================================
# Response Schemas (Saída)
# =====================================================================


class ScoreDimensaoSchema(BaseModel):
    valor: float
    peso_total_aplicado: float


class ScoreCompletoSchema(BaseModel):
    score_geral: ScoreDimensaoSchema
    score_por_dimensao: dict[str, ScoreDimensaoSchema]


class VincularLeadsSelfServiceResponse(BaseModel):
    """Resposta de POST /diagnosticos/vincular-leads-self-service (reatribuição de tenant)."""

    total_vinculados: int = Field(
        ge=0, description="Quantidade de diagnósticos reatribuídos ao tenant B2B."
    )
    diagnostico_ids: list[UUID] = Field(
        default_factory=list,
        description="Identificadores atualizados (ordem não garantida).",
    )


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
    empresa_faixa_faturamento: str | None = Field(
        default=None,
        description="Faixa de faturamento autodeclarada no POST (slug canónico), se informada.",
    )
    locale_relatorio: str = Field(
        default="pt-BR",
        description="Idioma usado na geração do PDF (persistido com o diagnóstico).",
    )
    score: ScoreCompletoSchema | None = None
    relatorio_pdf_url: str | None = None
    recomendacao_ia: str | None = None
    checklist: list[dict[str, Any]] | None = None
    matriz_impacto: list[dict[str, Any]] | None = None
    cronograma: list[dict[str, Any]] | None = None
    # M12 — estado persistido da autoconf (JSONB `checklist_m12_estado`)
    checklist_m12_autoconf: list[bool] | None = None
    # LGPD — instante registrado pelo servidor no POST (coluna `aceite_termos_privacidade_em`)
    aceite_termos_privacidade_em: datetime | None = None
    # Trilha de auditoria (persistência: hash_sha256, versao_otimista — LC 214/2025, ABNT NBR 17301:2026)
    hash_evidencia: str | None = None
    versao_otimista: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CnaeSubclasseItemSchema(BaseModel):
    """Uma subclass CNAE 2.3 (7 dígitos) para autocomplete."""

    subclasse_id: str = Field(..., min_length=7, max_length=7, pattern=r"^\d{7}$")
    descricao: str = Field(..., min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class CnaeBuscaResponse(BaseModel):
    """Resposta paginada leve do GET `/referencia/cnae/subclasses`."""

    itens: list[CnaeSubclasseItemSchema]
