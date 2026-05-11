"""
Repositório em memória para fluxo Playwright integrado em CI (login Postgres + lista real HTTP).

Camada: Infrastructure
Escopo: **somente** quando `QDI_CI_PLAYWRIGHT_INTEGRATED=1` e `APP_ENV=development`.

Não substitui Supabase em produção — analogia: dataset em memória para teste de integração,
como um `TClientDataSet` isolado no Delphi sem gravar no Oracle.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from src.application.services.plano_painel_derivacao import derivar_plano_painel_materializado
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.email_verificacao import codigo_store

_TENANT_PADRAO_CI = UUID("33333333-3333-4333-8333-333333333333")
_ID_LISTA_CI = UUID("22222222-2222-4222-a222-222222222222")


def _seed_diagnostico_demo() -> Diagnostico:
    """Um diagnóstico finalizado visível na listagem do painel (mesmo tenant do admin seed CI)."""
    return Diagnostico(
        id=_ID_LISTA_CI,
        tenant_id=_TENANT_PADRAO_CI,
        empresa=EmpresaInfo(
            cnpj="11222333000181",
            razao_social="Empresa Lista CI Integrado SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="6201500",
            uf="SP",
            setor_macro=SetorMacro.SERVICOS,
        ),
        respondente=Respondente(email="respondente@ci.integrado", nome="Respondente CI"),
        plano=PlanoDiagnostico.GRATUITO,
        status=StatusDiagnostico.FINALIZADO,
        criado_em=datetime(2026, 5, 5, 12, 0, tzinfo=UTC),
        finalizado_em=datetime(2026, 5, 5, 12, 5, tzinfo=UTC),
        score_geral=68.5,
        relatorio_pdf_url=None,
    )


class CiPlaywrightDiagnosticoRepository(DiagnosticoRepository):
    """Armazena apenas o seed fixo — suficiente para GET /diagnosticos/."""

    def __init__(self) -> None:
        self._rows: dict[UUID, Diagnostico] = {_ID_LISTA_CI: _seed_diagnostico_demo()}
        self._planos: dict[tuple[UUID, UUID], PlanoPainelSerializado] = {}
        self._subs_por_chave: dict[tuple[UUID, UUID, UUID], list[dict[str, Any]]] = {}

    async def salvar(self, diagnostico: Diagnostico) -> None:
        self._rows[diagnostico.id] = diagnostico

    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        row = self._rows.get(diagnostico_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    async def listar_por_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
        *,
        empresa_cnpj: str | None = None,
    ) -> list[Diagnostico]:
        items = [d for d in self._rows.values() if d.tenant_id == tenant_id]
        if empresa_cnpj:
            items = [d for d in items if d.empresa.cnpj == empresa_cnpj]
        items.sort(key=lambda d: d.criado_em, reverse=True)
        return items[offset : offset + limit]

    async def atualizar_relatorio_pdf_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        relatorio_pdf_url: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        row = await self.buscar_por_id(diagnostico_id, tenant_id)
        if row is None or row.versao_otimista != versao_esperada:
            return None
        row.anexar_relatorio(relatorio_pdf_url)
        row.versao_otimista += 1
        return row

    async def atualizar_checklist_m12_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        checklist_m12_estado: list[int],
        versao_esperada: int,
    ) -> Diagnostico | None:
        row = await self.buscar_por_id(diagnostico_id, tenant_id)
        if row is None or row.versao_otimista != versao_esperada:
            return None
        row.definir_checklist_m12_autoconf(checklist_m12_estado)
        row.versao_otimista += 1
        return row

    async def atualizar_quadro_implantacao_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        quadro_implantacao_anotacoes: dict[str, dict[str, Any]],
        versao_esperada: int,
    ) -> Diagnostico | None:
        row = await self.buscar_por_id(diagnostico_id, tenant_id)
        if row is None or row.versao_otimista != versao_esperada:
            return None
        row.definir_quadro_implantacao_anotacoes(quadro_implantacao_anotacoes)
        row.versao_otimista += 1
        return row

    def _merge_subtarefas_no_plano(
        self, plano: PlanoPainelSerializado, did: UUID, tid: UUID
    ) -> PlanoPainelSerializado:
        checklist_mut: list[dict[str, Any]] = []
        for frente in plano.checklist:
            acoes_mut: list[dict[str, Any]] = []
            for ac in frente.get("acoes", []):
                if not isinstance(ac, dict):
                    continue
                pid = ac.get("plano_acao_id")
                if not isinstance(pid, str):
                    acoes_mut.append(ac)
                    continue
                try:
                    aid = UUID(pid)
                except ValueError:
                    acoes_mut.append(ac)
                    continue
                chave = (did, tid, aid)
                subs = list(self._subs_por_chave.get(chave, ()))
                ac2 = {**ac, "subtarefas": subs}
                acoes_mut.append(ac2)
            checklist_mut.append({**frente, "acoes": acoes_mut})
        return PlanoPainelSerializado(
            versao_plano=plano.versao_plano,
            checklist=tuple(checklist_mut),
            matriz_impacto=plano.matriz_impacto,
            cronograma=plano.cronograma,
            subtarefas_por_acao=plano.subtarefas_por_acao,
        )

    async def salvar_e_materializar_plano_painel(
        self,
        diagnostico: Diagnostico,
        score_completo: ScoreCompleto,
        *,
        historico_campos_empresa_cnpj: list[tuple[str, str | None, str]] | None = None,
        cnpj_consulta_id: UUID | None = None,
    ) -> PlanoPainelSerializado:
        _ = historico_campos_empresa_cnpj
        _ = cnpj_consulta_id
        self._rows[diagnostico.id] = diagnostico
        deriv = derivar_plano_painel_materializado(diagnostico, score_completo)
        self._planos[(diagnostico.id, diagnostico.tenant_id)] = deriv.serializado_http
        return self._merge_subtarefas_no_plano(
            deriv.serializado_http, diagnostico.id, diagnostico.tenant_id
        )

    async def buscar_plano_painel_serializado(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        base = self._planos.get((diagnostico_id, tenant_id))
        if base is None:
            return None
        return self._merge_subtarefas_no_plano(base, diagnostico_id, tenant_id)

    async def materializar_plano_painel_idempotente_backfill(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        if (diagnostico_id, tenant_id) in self._planos:
            return None
        d = await self.buscar_por_id(diagnostico_id, tenant_id)
        if (
            d is None
            or d.status != StatusDiagnostico.FINALIZADO
            or d.score_completo_snapshot is None
        ):
            return None
        deriv = derivar_plano_painel_materializado(d, d.score_completo_snapshot)
        self._planos[(diagnostico_id, tenant_id)] = deriv.serializado_http
        return self._merge_subtarefas_no_plano(deriv.serializado_http, diagnostico_id, tenant_id)

    async def inserir_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        titulo: str,
        ordem: int = 0,
    ) -> dict[str, Any]:
        sid = uuid4()
        row = {
            "id": str(sid),
            "titulo": titulo.strip(),
            "status": "aberta",
            "prazo": None,
            "comentarios": None,
            "ordem": ordem,
        }
        chave = (diagnostico_id, tenant_id, plano_acao_id)
        self._subs_por_chave.setdefault(chave, []).append(row)
        return row

    async def atualizar_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        subtarefa_id: UUID,
        *,
        titulo: str | None = None,
        status: str | None = None,
        prazo: date | None = None,
        comentarios: str | None = None,
        ordem: int | None = None,
    ) -> dict[str, Any] | None:
        for chave, lst in self._subs_por_chave.items():
            if chave[0] != diagnostico_id or chave[1] != tenant_id:
                continue
            for i, row in enumerate(lst):
                if row.get("id") == str(subtarefa_id):
                    novo = dict(row)
                    if titulo is not None:
                        novo["titulo"] = titulo.strip()
                    if status is not None:
                        novo["status"] = status.strip()
                    if prazo is not None:
                        novo["prazo"] = prazo.isoformat()
                    if comentarios is not None:
                        novo["comentarios"] = comentarios
                    if ordem is not None:
                        novo["ordem"] = ordem
                    lst[i] = novo
                    return novo
        return None

    def vincular_leads_self_service_em_memoria(
        self,
        *,
        tenant_self_service: UUID,
        tenant_destino: UUID,
        email_admin_normalizado: str,
    ) -> list[UUID]:
        """
        Reatribui tenant no dict in-process (mesmos critérios do UPDATE em Postgres).

        Usado quando `QDI_CI_PLAYWRIGHT_INTEGRATED=1` — diagnósticos não passam pelo PostgREST.
        """
        email = codigo_store.normalizar_email(email_admin_normalizado)
        ids: list[UUID] = []
        for rid, d in list(self._rows.items()):
            if d.tenant_id != tenant_self_service:
                continue
            if d.plano != PlanoDiagnostico.GRATUITO:
                continue
            if codigo_store.normalizar_email(d.respondente.email) != email:
                continue
            self._rows[rid] = replace(d, tenant_id=tenant_destino)
            ids.append(rid)
        return ids
