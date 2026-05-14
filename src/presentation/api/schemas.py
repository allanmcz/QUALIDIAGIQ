"""
Schemas (DTOs) do Pydantic para validação HTTP.

Camada: Presentation
Responsabilidade:
    - Garantir que a API só receba payloads formatados corretamente.
    - Transformar objetos de Domínio puros em JSON limpo de saída.
"""

import re
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

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
            "M09 lead na plataforma; LGPD por finalidade."
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
        default="",
        max_length=18,
        description=(
            "CNPJ: **opcional** em fluxos só self-service (rascunho / OTP sem conta na plataforma). "
            "Vazio = sem cadastro PJ naquele ciclo. Se informado: 14 dígitos ou máscara, DV RFB válido. "
            "Com **sessão na plataforma** ou **vinculação de rascunho à conta**, o CNPJ é **obrigatório** "
            "(histórico por empresa no tenant) — ver `EmpresaPainelSchema` / ADR-013."
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
            return ""
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


class EmpresaPainelSchema(EmpresaSchema):
    """
    Empresa no pedido com **conta na plataforma** (JWT painel) ou **vinculação de rascunho à conta**.

    CNPJ obrigatório para permitir histórico fiável por PJ no tenant (LC 214/2025 — transparência
    operacional; LGPD em dados de empresa como contexto de negócio).
    """

    @model_validator(mode="after")
    def exigir_cnpj_para_historico_no_tenant(self) -> Self:
        if not self.cnpj or len(self.cnpj) != 14:
            raise ValueError(
                "CNPJ é obrigatório ao gravar diagnóstico com sessão na plataforma ou ao vincular "
                "rascunho à conta — necessário para histórico por empresa no tenant. "
                "No fluxo apenas com OTP (sem conta), use POST self-service / rascunho onde o CNPJ "
                "permanece opcional até à conclusão no ambiente self-service."
            )
        return self


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
    force_refresh_cnpj: bool = Field(
        default=False,
        description=(
            "Se verdadeiro e ``empresa.cnpj`` preenchido: nova consulta às fontes públicas ignorando TTL "
            "antes de fechar evidência WORM; merge com histórico em ``diagnostico_empresa_campo_historico``."
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


class IniciarDiagnosticoPainelRequest(IniciarDiagnosticoRequest):
    """Mesmo contrato que `IniciarDiagnosticoRequest`, com **CNPJ obrigatório** (painel / conta na plataforma)."""

    empresa: EmpresaPainelSchema


class RascunhoDiagnosticoSelfServiceResponse(BaseModel):
    """Resposta ao gravar rascunho no servidor (token opaco devolvido uma vez)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    resgate_token: str = Field(min_length=16, max_length=512)
    mensagem: str
    expira_em: datetime


class DiagnosticoRascunhoResumoResponse(BaseModel):
    """
    Metadados para a página de OTP.

    O portador do ``X-Rascunho-Token`` já provou posse do fluxo; incluímos o e-mail em claro para
    reenvio de código (paridade com /auth/verificar-email/solicitar).
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    empresa_razao_social: str
    empresa_cnpj: str = Field(
        default="",
        description="CNPJ normalizado no payload do rascunho (14 dígitos) ou vazio — UX antes de vincular à conta.",
    )
    email_mascarado: str
    # str (não EmailStr): valor já validado em POST /rascunho-self-service; EmailStr na resposta
    # causava 500 com e-mails aceites pelo wizard mas rejeitados pelo validador de saída (ex.: TLD dev).
    respondente_email: str = Field(
        ...,
        min_length=3,
        max_length=320,
        description="E-mail normalizado gravado no rascunho (mesmo usado em POST).",
    )
    expira_em: datetime


class ConcluirRascunhoDiagnosticoSelfServiceRequest(BaseModel):
    """OTP + token de resgate do rascunho persistido na BD."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    resgate_token: str = Field(min_length=16, max_length=512)
    codigo: str = Field(min_length=4, max_length=16)


class VincularRascunhoContaPlataformaRequest(BaseModel):
    """Associa rascunho self-service ao tenant do JWT (e-mail do respondente = e-mail do admin)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    resgate_token: str = Field(min_length=16, max_length=512)


class PatchRelatorioPdfRequest(BaseModel):
    """Corpo do PATCH que só altera a URL do relatório (lock otimista via If-Match)."""

    relatorio_pdf_url: str = Field(..., min_length=1, max_length=4096)


LikertM12Item = Annotated[
    int, Field(ge=1, le=5, description="Escala Likert 1 (minimo) a 5 (maximo).")
]


class PatchChecklistM12AutoconfRequest(BaseModel):
    """
    Corpo do PATCH M12 - espelho dos 10 controles ABNT (Likert 1-5 por item).

    Exige `If-Match` com `versao_otimista` atual (mesmo contrato do PATCH de relatório).
    """

    checklist_m12_autoconf: list[LikertM12Item] = Field(
        ...,
        min_length=10,
        max_length=10,
        description="Exatamente 10 inteiros 1-5 - mesma ordem das ações da frente ABNT no relatório.",
    )


class QuadroImplantacaoAnotacaoItemSchema(BaseModel):
    """Uma anotação por ação sugerida no quadro (chave f{i}_a{j} no mapa pai)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    comentario: str = Field(
        default="",
        max_length=8000,
        description="Legado: um único texto; use ``comentarios`` para várias notas.",
    )
    comentarios: list[str] = Field(
        default_factory=list,
        description="Lista de comentários (follow-ups) por ação; no máximo 30 itens.",
    )
    prazo_meta: str = Field(
        default="",
        max_length=32,
        description="Meta de prazo ISO YYYY-MM-DD ou vazio.",
    )
    descricao_personalizada: str = Field(
        default="",
        max_length=4000,
        description=(
            "Substitui a descrição canônica da ação no quadro (texto exibido ao consultor). "
            "Vazio = manter texto sugerido pelo motor."
        ),
    )

    @field_validator("comentarios", mode="before")
    @classmethod
    def comentarios_coerce_e_limites(cls, v: object) -> list[str]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("comentarios deve ser uma lista de strings.")
        limpos = [str(x).strip() for x in v if str(x).strip()]
        if len(limpos) > 30:
            raise ValueError("No máximo 30 comentários por ação sugerida.")
        for s in limpos:
            if len(s) > 2000:
                raise ValueError("Cada comentário deve ter no máximo 2000 caracteres.")
        return limpos

    @field_validator("prazo_meta")
    @classmethod
    def prazo_iso_ou_vazio(cls, v: str) -> str:
        s = (v or "").strip()
        if s == "":
            return ""
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            return s
        raise ValueError("prazo_meta deve ser data ISO YYYY-MM-DD ou vazio.")

    @field_validator("descricao_personalizada")
    @classmethod
    def descricao_personalizada_strip(cls, v: str) -> str:
        """Normaliza whitespace; teto 4000 vem de ``Field(max_length=...)`` (evita duplicar erro)."""
        return (v or "").strip()

    @model_validator(mode="after")
    def merge_comentario_legado_em_lista(self) -> Self:
        """Se veio só ``comentario`` (legado), reflete em ``comentarios`` para o restante da pipeline."""
        if self.comentarios:
            return self
        leg = self.comentario.strip()
        if leg:
            return self.model_copy(update={"comentarios": [leg]})
        return self


class PatchQuadroImplantacaoRequest(BaseModel):
    """Corpo do PATCH do quadro de implantação — exige ``If-Match`` com ``versao_otimista``."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    quadro_implantacao_anotacoes: dict[str, QuadroImplantacaoAnotacaoItemSchema] = Field(
        default_factory=dict,
        description=(
            "Mapa de anotações: chave legada f{i}_a{j} ou UUID ``plano_acao_id`` da ação materializada."
        ),
    )

    @field_validator("quadro_implantacao_anotacoes")
    @classmethod
    def validar_chaves_e_tamanho(
        cls, v: dict[str, QuadroImplantacaoAnotacaoItemSchema]
    ) -> dict[str, QuadroImplantacaoAnotacaoItemSchema]:
        if len(v) > 200:
            raise ValueError("No máximo 200 anotações no quadro de implantação.")
        pat_legado = re.compile(r"^f\d+_a\d+$")
        for k in v:
            ks = k.strip()
            if pat_legado.match(ks):
                continue
            try:
                UUID(ks)
            except ValueError as e:
                raise ValueError(
                    f"Chave inválida: {k!r}. Use UUID da ação materializada ou f{{índice}}_a{{índice}}."
                ) from e
        return v


class CriarSubtarefaPlanoDiagnosticoRequest(BaseModel):
    """Corpo do POST de subtarefa (plano materializado)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str = Field(min_length=1, max_length=500)
    ordem: int = Field(default=0, ge=0, le=10_000)


class PatchSubtarefaPlanoDiagnosticoRequest(BaseModel):
    """Corpo do PATCH de subtarefa — todos os campos opcionais (parcial)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    titulo: str | None = Field(default=None, max_length=500)
    status: str | None = Field(default=None, max_length=32)
    prazo: date | None = None
    comentarios: str | None = Field(default=None, max_length=8000)
    ordem: int | None = Field(default=None, ge=0, le=10_000)


class LgpdTitularSolicitacaoPayload(BaseModel):
    """Metadados estruturados da solicitação (art. 18 LGPD) — QDI-H-013."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    motivo: str | None = Field(default=None, max_length=4000)
    detalhes: str | None = Field(default=None, max_length=8000)
    idioma_resposta: str | None = Field(default=None, max_length=16)
    referencia_diagnostico_texto: str | None = Field(default=None, max_length=500)


class RegistrarSolicitacaoTitularLgpdRequest(BaseModel):
    """Corpo do POST /privacidade/solicitacoes (art. 18)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    diagnostico_id: UUID | None = Field(
        default=None,
        description="Opcional: vínculo com um diagnóstico específico no tenant.",
    )
    tipo: str = Field(
        ...,
        min_length=3,
        max_length=32,
        description="acesso, correcao, anonimizacao, eliminacao, portabilidade ou oposicao.",
    )
    canal: str = Field(
        default="plataforma",
        min_length=4,
        max_length=24,
        description="plataforma, self_service ou dpo_email.",
    )
    solicitante_email: str = Field(..., min_length=5, max_length=254)
    payload: LgpdTitularSolicitacaoPayload = Field(
        default_factory=LgpdTitularSolicitacaoPayload,
        description="Metadados estruturados da solicitação (campos conhecidos; extra proibido).",
    )


class AtualizarStatusSolicitacaoTitularLgpdRequest(BaseModel):
    """PATCH operacional de status da solicitação."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    status: str = Field(
        ...,
        min_length=4,
        max_length=24,
        description="recebida, em_analise, deferida, indeferida ou concluida.",
    )
    observacao_interna: str | None = Field(default=None, max_length=4000)


class SolicitacaoTitularLgpdResponse(BaseModel):
    """Resposta HTTP da solicitação LGPD registrada."""

    id: UUID
    tenant_id: UUID
    diagnostico_id: UUID | None
    tipo: str
    status: str
    canal: str
    solicitante_email: str
    payload: JsonValue
    observacao_interna: str | None
    actor_user_id: UUID | None
    criado_em: datetime
    atualizado_em: datetime


class AnonimizarRespondenteLgpdHttpRequest(BaseModel):
    """POST /privacidade/diagnosticos/{id}/anonimizar-respondente — exige solicitação ``deferida``."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    solicitacao_id: UUID = Field(
        ...,
        description="Identificador da linha em lgpd_titular_solicitacao (tipo anonimizacao, status deferida).",
    )


class AnonimizarRespondenteLgpdHttpResponse(BaseModel):
    """Confirmação após transação (log + UPDATE diagnóstico + conclusão da solicitação)."""

    diagnostico_id: UUID
    solicitacao_id: UUID
    status_solicitacao: str = "concluida"
    mensagem: str = (
        "Anonimização dos campos do respondente aplicada; registo em lgpd_anonimizacao_log "
        "(email sentinel + nome marcador + remoção de cargo/telefone)."
    )


class EliminarDiagnosticoLgpdHttpRequest(BaseModel):
    """POST /privacidade/diagnosticos/{id}/eliminar-diagnostico — exige solicitação ``deferida``."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    solicitacao_id: UUID = Field(
        ...,
        description="Identificador da linha em lgpd_titular_solicitacao (tipo eliminacao, status deferida).",
    )


class EliminarDiagnosticoLgpdHttpResponse(BaseModel):
    """Confirmação após DELETE do diagnóstico (pré-finalização) e conclusão da solicitação."""

    diagnostico_id: UUID
    solicitacao_id: UUID
    status_solicitacao: str = "concluida"
    mensagem: str = (
        "Diagnóstico eliminado fisicamente (estados em_andamento, cancelado ou expirado); "
        "solicitação LGPD concluída."
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


class PesoMacroNormativaItemSchema(BaseModel):
    """
    Peso macro por dimensão com vigência resolvida na data UTC do pedido (M03).

    LC 214/2025 art. 5º — previsibilidade; em Postgres: linha efetiva de ``normativa_score_macro_dimensao``.
    """

    peso: float = Field(..., gt=0, description="Peso macro aplicado na agregação do score geral.")
    vigencia_inicio: date = Field(
        ...,
        description="Início da vigência da linha normativa efetiva (inclusive).",
    )
    vigencia_fim: date | None = Field(
        default=None,
        description="Fim da vigência (inclusive) ou null quando vigência aberta.",
    )
    rotulo_versao: str | None = Field(
        default=None,
        description="Rótulo editorial da versão (ex.: baseline-m03-qdi-2026).",
    )


class NormativaPesoPerguntaOverlaySchema(BaseModel):
    """
    Transparência quando o peso efetivo substitui o do catálogo JSON (Postgres).

    Tabela: ``qdi.normativa_pergunta_peso`` (migração 0042). LC 214/2025 art. 5º — previsibilidade.
    """

    peso_catalogo_json: float = Field(
        ...,
        description="Peso publicado no ficheiro `perguntas_mvp.json` antes do overlay.",
    )
    peso_normativo_db: float = Field(
        ...,
        gt=0,
        description="Peso aplicado (linha vigente na data do pedido).",
    )
    vigencia_inicio: date = Field(
        ...,
        description="Início da vigência da linha normativa (inclusive).",
    )
    vigencia_fim: date | None = Field(
        default=None,
        description="Fim da vigência (inclusive) ou null quando vigência aberta.",
    )
    rotulo_versao: str | None = Field(
        default=None,
        description="Rótulo editorial da versão normativa (ex.: overlay-m03-qdi-2026).",
    )


class ManifestoPesoPerguntaSchema(BaseModel):
    """Um item do catálogo com peso explícito (transparência M03)."""

    codigo: str = Field(..., description="Código canônico da pergunta (ex.: Q-EST-001).")
    dimensao: str = Field(
        ...,
        description="Dimensão ABNT / score (fiscal, estrategica, tecnologica, etc.).",
    )
    tipo: str = Field(..., description="Tipo de resposta (ternaria, binaria, escala_1_5, ...).")
    peso: float = Field(
        ..., description="Peso no cálculo dentro da dimensão (após overlay DB, se houver)."
    )
    base_legal: str | None = Field(
        default=None,
        description="Referência normativa associada à pergunta (LC 214/2025, NT, EC 132/2023, ...).",
    )
    pilar_abnt: str | None = Field(
        default=None,
        description="Pilar/tema ABNT NBR 17301:2026 opcional (catálogo versionado).",
    )
    normativa_overlay: NormativaPesoPerguntaOverlaySchema | None = Field(
        default=None,
        description="Metadados da linha Postgres quando o peso efetivo não é só o do JSON.",
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
                "pesos_macro_dimensao_normativa": {
                    "fiscal": {
                        "peso": 1.5,
                        "vigencia_inicio": "2026-01-01",
                        "vigencia_fim": None,
                        "rotulo_versao": "baseline-m03-qdi-2026",
                    },
                },
                "perguntas": [
                    {
                        "codigo": "Q-EST-001",
                        "dimensao": "estrategica",
                        "tipo": "ternaria",
                        "peso": 7.5,
                        "base_legal": "EC 132/2023; LC 214/2025",
                        "normativa_overlay": None,
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
    pesos_macro_dimensao_normativa: dict[str, PesoMacroNormativaItemSchema] = Field(
        ...,
        description=(
            "Mesmos pesos que `pesos_macro_dimensao`, com `vigencia_inicio` / `vigencia_fim` e rótulo "
            "da linha normativa efetiva na data do pedido (auditoria M03)."
        ),
    )
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
                "pesos_macro_dimensao_normativa": {
                    "fiscal": {
                        "peso": 1.5,
                        "vigencia_inicio": "2026-01-01",
                        "vigencia_fim": None,
                        "rotulo_versao": "baseline-m03-qdi-2026",
                    },
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
    pesos_macro_dimensao_normativa: dict[str, PesoMacroNormativaItemSchema] = Field(
        ...,
        description="Rasto de vigência por dimensão — mesma resolução que o motor na data UTC do pedido.",
    )
    nota_metodologica: str = Field(
        ...,
        description="Texto explicando a relação entre pesos macro e pesos do catálogo por pergunta.",
    )
    recomendacoes_gaps_criticos: list[str] = Field(
        default_factory=list,
        description="Alertas heurísticos para leitura executiva (não vinculam obrigação legal).",
    )


class InstitucionalPublicResponse(BaseModel):
    """Conteúdo de GET /public/institucional — canal DPO e referências LGPD configuradas na API."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lgpd_dpo_email": "allan@tributolab.com.br",
                "lgpd_retencao_referencia_dias": 180,
                "privacidade_solicitacoes_path": "/privacidade/solicitacoes",
            },
        },
    )

    lgpd_dpo_email: str | None = Field(
        default=None,
        description="E-mail do encarregado (LGPD) definido na API; espelhar no front com NEXT_PUBLIC_LGPD_DPO_EMAIL.",
    )
    lgpd_retencao_referencia_dias: int = Field(
        ...,
        ge=1,
        description=(
            "Valor operacional de LGPD_RETENTION_DAYS na API (referência para políticas internas; "
            "a Política de Privacidade publicada prevalece)."
        ),
    )
    privacidade_solicitacoes_path: str = Field(
        default="/privacidade/solicitacoes",
        description=(
            "Caminho relativo dos endpoints autenticados de solicitação LGPD do titular "
            "(migração 0028, Bearer + Idempotency-Key no POST)."
        ),
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
        ge=0,
        description="Quantidade de diagnósticos reatribuídos ao tenant da conta na plataforma.",
    )
    diagnostico_ids: list[UUID] = Field(
        default_factory=list,
        description="Identificadores atualizados (ordem não garantida).",
    )


class DiagnosticoConclusaoPublicaDimensaoSchema(BaseModel):
    """Uma dimensão no breakdown público pós-conclusão self-service."""

    dimensao: str
    valor: float
    peso_total_aplicado: float | None = None

    model_config = ConfigDict(str_strip_whitespace=True)


class DiagnosticoConclusaoSelfServicePublicoResponse(BaseModel):
    """
    Snapshot mínimo para a página pública de conclusão (sem JWT).

    Dados lidos de ``diagnosticos`` após validação do token de leitura na tabela dedicada.
    """

    id: UUID
    status: str
    empresa_razao_social: str
    locale_relatorio: str = Field(default="pt-BR")
    score_geral: float | None = None
    scores_por_dimensao: list[DiagnosticoConclusaoPublicaDimensaoSchema] = Field(
        default_factory=list
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class DiagnosticoResumoSchema(BaseModel):
    """Item resumido para listagem do tenant (P7 — painel)."""

    id: UUID
    empresa_razao_social: str
    empresa_cnpj: str = Field(
        default="",
        description="CNPJ normalizado (14 dígitos) ou vazio — agrupa ciclos «antes/depois» no painel.",
    )
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
    empresa_cnpj: str = Field(
        default="",
        description="CNPJ no snapshot do diagnóstico (14 dígitos ou vazio se não informado).",
    )
    criado_em: datetime | None = Field(
        default=None,
        description="Instante de criação (UTC) — útil para linha do tempo e comparativo entre ciclos.",
    )
    finalizado_em: datetime | None = Field(
        default=None,
        description="Instante de finalização (UTC), se aplicável.",
    )
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
    # M12 - estado persistido da autoconf (JSONB `checklist_m12_estado`, Likert 1-5)
    checklist_m12_autoconf: list[int] | None = None
    # Quadro de implantação — anotações consultor (JSONB `quadro_implantacao_anotacoes`)
    quadro_implantacao_anotacoes: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description="Mapa f{i}_a{j} -> {prazo_meta, comentarios[]} (legado comentario migrado na leitura).",
    )
    # LGPD — instante registrado pelo servidor no POST (coluna `aceite_termos_privacidade_em`)
    aceite_termos_privacidade_em: datetime | None = None
    # Trilha de auditoria (persistência: hash_sha256, versao_otimista — LC 214/2025, ABNT NBR 17301:2026)
    hash_evidencia: str | None = None
    versao_otimista: int | None = None
    versao_plano: int = Field(
        default=1,
        ge=1,
        description="Versão do snapshot do plano de ação materializado (checklist/matriz/cronograma).",
    )
    leitura_token: str | None = Field(
        default=None,
        description=(
            "Presente só em POST /diagnosticos/rascunho-self-service/concluir: token opaco para "
            "GET /diagnosticos/self-service/conclusao-visualizacao (leitura pública limitada no tempo)."
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class CnaeSubclasseItemSchema(BaseModel):
    """Uma subclass CNAE 2.3 (7 dígitos) para autocomplete."""

    subclasse_id: str = Field(..., min_length=7, max_length=7, pattern=r"^\d{7}$")
    descricao: str = Field(..., min_length=1)

    model_config = ConfigDict(str_strip_whitespace=True)


class CnaeBuscaResponse(BaseModel):
    """Resposta paginada leve do GET `/referencia/cnae/subclasses`."""

    itens: list[CnaeSubclasseItemSchema]


class ConsultarCnpjRequest(BaseModel):
    """Corpo POST `/referencia/cnpj/consulta_cnpj` — exige JWT com ``tenant_id``."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    cnpj: str = Field(
        ...,
        min_length=14,
        max_length=18,
        description="CNPJ com ou sem máscara — armazenado e consultado com 14 dígitos.",
    )
    force_refresh: bool = Field(
        default=False,
        description="Ignora cache TTL e força nova chamada às fontes públicas.",
    )
    aplicar_no_diagnostico_id: UUID | None = Field(
        default=None,
        description=(
            "Se informado: merge nos campos empresa_* apenas quando o diagnóstico está "
            "``em_andamento`` (WORM bloqueia alteração pós-finalização)."
        ),
    )

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj_consulta(cls, v: str) -> str:
        raw = normalizar_cnpj_apenas_digitos(v or "")
        if len(raw) != 14:
            raise ValueError("CNPJ deve conter exatos 14 dígitos numéricos")
        if len(set(raw)) == 1:
            raise ValueError("CNPJ inválido")
        if not cnpj_com_digitos_verificadores_validos(raw):
            raise ValueError("CNPJ inválido: dígitos verificadores não conferem")
        return raw


class CnpjCanonicoResponse(BaseModel):
    """Recorte canónico persistido em ``cnpj_consultas.payload_canonico`` (volatilidades TTL)."""

    model_config = ConfigDict(extra="forbid")

    cnpj: str
    razao_social: str | None = None
    nome_fantasia: str | None = None
    cnae_principal: str | None = None
    uf: str | None = None
    situacao_cadastral: str | None = None
    porte: str | None = None
    regime: str | None = None
    setor_macro: str | None = None
    municipio: str | None = None
    logradouro: str | None = None


class ConsultarCnpjResponse(BaseModel):
    """Resposta à consulta materializada (idempotente por ``Idempotency-Key`` + tenant)."""

    consulta_id: UUID
    cnpj: str
    fonte: str = Field(description="``brasil_api`` ou ``minha_receita``.")
    canonico: CnpjCanonicoResponse
    expira_cadastral_em: datetime
    expira_qualificacao_em: datetime
    expira_situacao_em: datetime
    aplicado_em_diagnostico_em_andamento: bool = False


class FormatoExportPortabilidade(StrEnum):
    """Formato do pacote de export (ADR-012 §4)."""

    json = "json"
    pacote_pdf = "pacote_pdf"


class RegistrarRetificacaoDiagnosticoRequest(BaseModel):
    """POST retificação append-only (cadeia NF-e/CC-e — ADR-012 §5)."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    motivo_retificacao: str = Field(..., min_length=10, max_length=8000)
    payload_retificacao: dict[str, Any] = Field(default_factory=dict)


class DiagnosticoRetificacaoHttpResponse(BaseModel):
    """Linha de retificação persistida."""

    id: UUID
    tenant_id: UUID
    diagnostico_original_id: UUID
    hash_diagnostico_original_sha256: str
    motivo_retificacao: str
    payload_retificacao: dict[str, Any]
    hash_retificacao_sha256: str
    actor_user_id: UUID | None
    criado_em: datetime
