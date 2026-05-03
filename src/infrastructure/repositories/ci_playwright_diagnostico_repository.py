"""
Repositório em memória para fluxo Playwright integrado em CI (login Postgres + lista real HTTP).

Camada: Infrastructure
Escopo: **somente** quando `QDI_CI_PLAYWRIGHT_INTEGRATED=1` e `APP_ENV=development`.

Não substitui Supabase em produção — analogia: dataset em memória para teste de integração,
como um `TClientDataSet` isolado no Delphi sem gravar no Oracle.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

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
from src.infrastructure.email_verificacao import codigo_store

_TENANT_PADRAO_CI = UUID("33333333-3333-4333-8333-333333333333")
_ID_LISTA_CI = UUID("22222222-2222-4222-a222-222222222222")


def _seed_diagnostico_demo() -> Diagnostico:
    """Um diagnóstico finalizado visível na listagem B2B (mesmo tenant do admin seed CI)."""
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

    async def salvar(self, diagnostico: Diagnostico) -> None:
        self._rows[diagnostico.id] = diagnostico

    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        row = self._rows.get(diagnostico_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        return row

    async def listar_por_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Diagnostico]:
        items = [d for d in self._rows.values() if d.tenant_id == tenant_id]
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
        checklist_m12_estado: list[bool],
        versao_esperada: int,
    ) -> Diagnostico | None:
        row = await self.buscar_por_id(diagnostico_id, tenant_id)
        if row is None or row.versao_otimista != versao_esperada:
            return None
        row.definir_checklist_m12_autoconf(checklist_m12_estado)
        row.versao_otimista += 1
        return row

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
