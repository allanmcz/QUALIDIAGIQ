"""
Adapter Supabase para o port DiagnosticoRepository.

Camada: Infrastructure
Implementa: src.domain.repositories.diagnostico_repository.DiagnosticoRepository

Princípios:
    - Multi-tenant via Row Level Security (RLS) — nunca usar service_role nesta camada
    - Idempotência em `salvar` (upsert por `id`)
    - Tradução entre dataclass de domínio ↔ dict do Supabase

Implementação:
    O pacote `supabase-py` expõe cliente **síncrono** (`Client`). Os métodos do port são
    **async** para não bloquear o event loop do FastAPI — chamadas ao PostgREST rodam em
    `asyncio.to_thread` (analogia: `TThread` no Delphi executando query síncrona).

Analogia para o Allan:
    Equivale ao seu DataModule no Delphi que encapsulava todos os
    TFDQuery/TZQuery — separa a "ferida" do banco do código de regras.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.score import ScoreCompleto

if TYPE_CHECKING:
    from supabase import Client


class SupabaseDiagnosticoRepository(DiagnosticoRepository):
    """Adapter concreto que persiste em Supabase (PostgreSQL + RLS)."""

    def __init__(self, client: Client) -> None:
        """
        Args:
            client: Cliente Supabase síncrono (`create_client`) com JWT de tenant válido.
        """
        self._client = client

    async def salvar(self, diagnostico: Diagnostico) -> None:
        """Upsert idempotente — valida RLS no servidor."""
        payload = self._para_dict(diagnostico)

        def _upsert() -> None:
            self._client.table("diagnosticos").upsert(payload).execute()

        await asyncio.to_thread(_upsert)

    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        """Busca por ID com tenant_id como filtro adicional (defense-in-depth)."""
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _select() -> Any:
            return (
                self._client.table("diagnosticos")
                .select("*")
                .eq("id", sid)
                .eq("tenant_id", stid)
                .execute()
            )

        response = await asyncio.to_thread(_select)
        data = response.data
        if not data:
            return None
        return self._para_entity(data[0])

    async def listar_por_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Diagnostico]:
        """Listagem paginada por tenant."""
        stid = str(tenant_id)

        def _select() -> Any:
            return (
                self._client.table("diagnosticos")
                .select("*")
                .eq("tenant_id", stid)
                .order("criado_em", desc=True)
                .limit(limit)
                .offset(offset)
                .execute()
            )

        response = await asyncio.to_thread(_select)
        return [self._para_entity(row) for row in response.data]

    async def atualizar_relatorio_pdf_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        relatorio_pdf_url: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        """UPDATE condicional em `versao_otimista` (PostgREST `select` pós-update)."""
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _update() -> Any:
            # postgrest-py: encadear `.select` após filtros — stubs não expõem o builder unificado
            q: Any = (
                self._client.table("diagnosticos")
                .update(
                    {
                        "relatorio_pdf_url": relatorio_pdf_url,
                        "versao_otimista": versao_esperada + 1,
                    }
                )
                .eq("id", sid)
                .eq("tenant_id", stid)
                .eq("versao_otimista", versao_esperada)
            )
            return q.select("*").execute()

        response = await asyncio.to_thread(_update)
        data = response.data
        if not data:
            return None
        return self._para_entity(data[0])

    async def atualizar_checklist_m12_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        checklist_m12_estado: list[bool],
        versao_esperada: int,
    ) -> Diagnostico | None:
        """UPDATE condicional do JSONB M12 + incremento de `versao_otimista`."""
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _update() -> Any:
            q: Any = (
                self._client.table("diagnosticos")
                .update(
                    {
                        "checklist_m12_estado": checklist_m12_estado,
                        "versao_otimista": versao_esperada + 1,
                    }
                )
                .eq("id", sid)
                .eq("tenant_id", stid)
                .eq("versao_otimista", versao_esperada)
            )
            return q.select("*").execute()

        response = await asyncio.to_thread(_update)
        data = response.data
        if not data:
            return None
        return self._para_entity(data[0])

    # ============================================================
    # Tradução entity ↔ dict
    # ============================================================

    def _para_dict(self, d: Diagnostico) -> dict[str, Any]:
        """Serializa entidade para o formato JSONB do Supabase."""
        score_blob = (
            d.score_completo_snapshot.para_dict_serializavel()
            if d.score_completo_snapshot is not None
            else None
        )
        return {
            "id": str(d.id),
            "tenant_id": str(d.tenant_id),
            "respondente_email": d.respondente.email if d.respondente else None,
            "respondente_nome": d.respondente.nome if d.respondente else None,
            "respondente_cargo": d.respondente.cargo if d.respondente else None,
            "respondente_telefone": d.respondente.telefone if d.respondente else None,
            "empresa_cnpj": d.empresa.cnpj,
            "empresa_razao_social": d.empresa.razao_social,
            "empresa_porte": d.empresa.porte.value,
            "empresa_regime": d.empresa.regime.value,
            "empresa_cnae": d.empresa.cnae_principal,
            "empresa_uf": d.empresa.uf,
            "empresa_setor_macro": d.empresa.setor_macro.value,
            "status": d.status.value,
            "plano": d.plano.value,
            "score_geral": d.score_geral,
            "relatorio_pdf_url": d.relatorio_pdf_url,
            "criado_em": d.criado_em.isoformat(),
            "finalizado_em": d.finalizado_em.isoformat() if d.finalizado_em else None,
            "hash_sha256": d.hash_evidencia,
            "score_completo": score_blob,
            "versao_otimista": d.versao_otimista,
            "checklist_m12_estado": d.checklist_m12_estado,
        }

    def _para_entity(self, row: dict[str, Any]) -> Diagnostico:
        """Desserializa dict do banco para a entidade."""
        from src.domain.entities.diagnostico import PlanoDiagnostico

        raw_created = row.get("criado_em")
        criado_em = (
            datetime.fromisoformat(str(raw_created).replace("Z", "+00:00")) if raw_created else None
        )
        raw_fin = row.get("finalizado_em")
        finalizado_em = (
            datetime.fromisoformat(str(raw_fin).replace("Z", "+00:00")) if raw_fin else None
        )

        snap: ScoreCompleto | None = None
        sc_raw = row.get("score_completo")
        if isinstance(sc_raw, dict):
            try:
                snap = ScoreCompleto.desde_dict(sc_raw)
            except (KeyError, TypeError, ValueError):
                snap = None

        email_resp = row.get("respondente_email") or "nao-informado@placeholder.qdi"

        m12_raw = row.get("checklist_m12_estado")
        checklist_m12: list[bool] | None = None
        if isinstance(m12_raw, list):
            try:
                checklist_m12 = [bool(x) for x in m12_raw]
            except (TypeError, ValueError):
                checklist_m12 = None

        return Diagnostico(
            id=UUID(row["id"]),
            tenant_id=UUID(row["tenant_id"]),
            empresa=EmpresaInfo(
                cnpj=row["empresa_cnpj"],
                razao_social=row["empresa_razao_social"],
                porte=PorteEmpresa(row["empresa_porte"]),
                regime=RegimeTributario(row["empresa_regime"]),
                cnae_principal=row["empresa_cnae"],
                uf=row["empresa_uf"],
                setor_macro=SetorMacro(row["empresa_setor_macro"]),
            ),
            respondente=Respondente(
                email=email_resp,
                nome=row.get("respondente_nome"),
                cargo=row.get("respondente_cargo"),
                telefone=row.get("respondente_telefone"),
            ),
            status=StatusDiagnostico(row["status"]),
            plano=PlanoDiagnostico(row.get("plano", "gratuito")),
            criado_em=criado_em if criado_em is not None else datetime.now(UTC),
            finalizado_em=finalizado_em,
            score_geral=row.get("score_geral"),
            relatorio_pdf_url=row.get("relatorio_pdf_url"),
            score_completo_snapshot=snap,
            hash_evidencia=row.get("hash_sha256"),
            versao_otimista=int(row.get("versao_otimista") or 1),
            checklist_m12_estado=checklist_m12,
        )
