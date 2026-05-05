"""
Deriva checklist / matriz / cronograma com identificadores estáveis para persistência e API.

Camada: Application (usa ``ConsultoriaService`` — motor editorial normativo).

Analogia: como montar um ``TClientDataSet`` em memória antes do ``ApplyUpdates`` no Oracle —
aqui geramos UUID por linha de ação para o painel não depender de ``f{i}_a{j}``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID, uuid4

from src.application.services.consultoria_service import ConsultoriaService
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import ScoreCompleto


def _origem_motor_por_nome_frente(nome_frente: str) -> str:
    """Classificação editorial grossa para auditoria (M07, ABNT10, etc.)."""
    n = nome_frente.strip()
    if "lacunas" in n.lower() or n.startswith("Prioridade"):
        return "M07"
    if "Governança e Comitê" in n or n.startswith("Governança"):
        return "GOVERNANCA"
    if "TI / ERP" in n or "Sistema Fiscal" in n:
        return "TI_ERP"
    if "Cadastros" in n:
        return "CADASTROS"
    if "Contratos" in n:
        return "CONTRATOS"
    if "17301" in n or "ABNT" in n:
        return "ABNT10"
    return "OUTROS"


@dataclass(frozen=True, slots=True)
class LinhaPlanoAcaoParaPersistir:
    """Uma linha de ``diagnostico_plano_acao`` antes do INSERT (IDs já definidos)."""

    id: UUID
    ordem_exibicao: int
    frente_indice: int
    acao_indice: int
    frente_nome: str
    texto_acao: str
    responsavel_sugerido: str
    prazo_sugerido_texto: str
    criticidade: str
    base_legal: str | None
    origem_motor: str
    prioridade_motor: int


@dataclass(frozen=True, slots=True)
class LinhaPlanoMatrizParaPersistir:
    """Uma linha de ``diagnostico_plano_matriz``."""

    id: UUID
    ordem_exibicao: int
    departamento: str
    impacto_resumo: str
    criticidade: str
    base_legal: str | None


@dataclass(frozen=True, slots=True)
class LinhaPlanoCronogramaParaPersistir:
    """Uma linha de ``diagnostico_plano_cronograma``."""

    id: UUID
    ordem_exibicao: int
    fase: str
    foco: str
    referencia_normativa: str


@dataclass(frozen=True, slots=True)
class DerivacaoPlanoMaterializado:
    """Resultado único da derivação — persiste na BD e alimenta o contrato HTTP."""

    versao_plano: int
    linhas_acao: tuple[LinhaPlanoAcaoParaPersistir, ...]
    linhas_matriz: tuple[LinhaPlanoMatrizParaPersistir, ...]
    linhas_cronograma: tuple[LinhaPlanoCronogramaParaPersistir, ...]
    serializado_http: PlanoPainelSerializado


def derivar_plano_painel_materializado(
    diagnostico: Diagnostico,
    score_completo: ScoreCompleto,
    *,
    versao_plano: int = 1,
) -> DerivacaoPlanoMaterializado:
    """
    Gera linhas de INSERT + payload HTTP com ``plano_acao_id`` e chave legada ``chave_quadro_legado``.

    A ordem de frentes e ações replica ``ConsultoriaService.gerar_checklist`` (incl. ``sort`` por prioridade).
    """
    frentes = ConsultoriaService.gerar_checklist(diagnostico, score_completo)
    matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
    cronograma_raw = ConsultoriaService.gerar_cronograma_cinco_fases()

    linhas_acao: list[LinhaPlanoAcaoParaPersistir] = []
    checklist_http: list[dict[str, Any]] = []
    ordem = 0

    for fi, frente in enumerate(frentes):
        origem = _origem_motor_por_nome_frente(frente.nome)
        acoes_http: list[dict[str, Any]] = []
        for aj, acao in enumerate(frente.acoes):
            aid = uuid4()
            linhas_acao.append(
                LinhaPlanoAcaoParaPersistir(
                    id=aid,
                    ordem_exibicao=ordem,
                    frente_indice=fi,
                    acao_indice=aj,
                    frente_nome=frente.nome,
                    texto_acao=acao.descricao,
                    responsavel_sugerido=acao.responsavel,
                    prazo_sugerido_texto=acao.prazo,
                    criticidade=acao.criticidade,
                    base_legal=acao.base_legal,
                    origem_motor=origem,
                    prioridade_motor=acao.prioridade,
                )
            )
            d_acao = asdict(acao)
            d_acao["plano_acao_id"] = str(aid)
            d_acao["chave_quadro_legado"] = f"f{fi}_a{aj}"
            acoes_http.append(d_acao)
            ordem += 1
        checklist_http.append({"nome": frente.nome, "acoes": acoes_http})

    linhas_matriz: list[LinhaPlanoMatrizParaPersistir] = []
    for mi, m in enumerate(matriz_entities):
        linhas_matriz.append(
            LinhaPlanoMatrizParaPersistir(
                id=uuid4(),
                ordem_exibicao=mi,
                departamento=m.departamento,
                impacto_resumo=m.impacto_resumo,
                criticidade=m.criticidade,
                base_legal=m.base_legal,
            )
        )

    linhas_cronograma: list[LinhaPlanoCronogramaParaPersistir] = []
    for ci, row in enumerate(cronograma_raw):
        linhas_cronograma.append(
            LinhaPlanoCronogramaParaPersistir(
                id=uuid4(),
                ordem_exibicao=ci,
                fase=str(row.get("fase", "")),
                foco=str(row.get("foco", "")),
                referencia_normativa=str(row.get("referencia_normativa", "")),
            )
        )

    matriz_http = [asdict(m) for m in matriz_entities]
    serializado = PlanoPainelSerializado(
        versao_plano=versao_plano,
        checklist=tuple(checklist_http),
        matriz_impacto=tuple(matriz_http),
        cronograma=tuple(dict(r) for r in cronograma_raw),
        subtarefas_por_acao={},
    )
    return DerivacaoPlanoMaterializado(
        versao_plano=versao_plano,
        linhas_acao=tuple(linhas_acao),
        linhas_matriz=tuple(linhas_matriz),
        linhas_cronograma=tuple(linhas_cronograma),
        serializado_http=serializado,
    )
