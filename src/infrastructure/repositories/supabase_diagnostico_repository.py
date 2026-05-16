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
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PainelEstadoCicloDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.checklist_m12_likert import normalizar_checklist_m12_estado_bruto
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.resultado_eliminacao_empresa import ResultadoEliminacaoEmpresa
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.repositories.supabase_plano_painel_sync import (
    atualizar_subtarefa_supabase,
    buscar_plano_painel_serializado_supabase,
    inserir_subtarefa_supabase,
    materializar_plano_painel_supabase,
)

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
        self._explicacao_historico_mem: dict[tuple[str, str], list[dict[str, Any]]] = {}

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
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
        *,
        empresa_cnpj: str | None = None,
    ) -> list[Diagnostico]:
        """Listagem paginada por tenant."""
        stid = str(tenant_id)

        def _select() -> Any:
            q: Any = self._client.table("diagnosticos").select("*").eq("tenant_id", stid)
            if empresa_cnpj:
                q = q.eq("empresa_cnpj", empresa_cnpj)
            return q.order("criado_em", desc=True).limit(limit).offset(offset).execute()

        response = await asyncio.to_thread(_select)
        return [self._para_entity(row) for row in response.data]

    async def eliminar_diagnosticos_empresa_eliminaveis(
        self,
        tenant_id: UUID,
        empresa_cnpj: str,
        *,
        actor_user_id: UUID | None = None,
    ) -> ResultadoEliminacaoEmpresa:
        _ = actor_user_id
        stid = str(tenant_id)
        statuses_eliminaveis = ("em_andamento", "cancelado", "expirado")

        def _select_ids() -> Any:
            return (
                self._client.table("diagnosticos")
                .select("id, status")
                .eq("tenant_id", stid)
                .eq("empresa_cnpj", empresa_cnpj)
                .execute()
            )

        response = await asyncio.to_thread(_select_ids)
        eliminados: list[UUID] = []
        mantidos_finalizados = 0
        mantidos_outros = 0
        for row in response.data:
            st = str(row.get("status", ""))
            rid = UUID(str(row["id"]))
            if st == "finalizado":
                mantidos_finalizados += 1
            elif st in statuses_eliminaveis:

                def _delete_one(diagnostico_id: str = str(rid)) -> Any:
                    return (
                        self._client.table("diagnosticos")
                        .delete()
                        .eq("id", diagnostico_id)
                        .eq("tenant_id", stid)
                        .execute()
                    )

                del_resp = await asyncio.to_thread(_delete_one)
                if del_resp.data:
                    eliminados.append(rid)
            else:
                mantidos_outros += 1
        return ResultadoEliminacaoEmpresa(
            empresa_cnpj=empresa_cnpj,
            eliminados_ids=tuple(eliminados),
            mantidos_finalizados=mantidos_finalizados,
            mantidos_outros_status=mantidos_outros,
        )

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
        checklist_m12_estado: list[int],
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

    async def atualizar_quadro_implantacao_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        quadro_implantacao_anotacoes: dict[str, dict[str, Any]],
        versao_esperada: int,
    ) -> Diagnostico | None:
        """UPDATE condicional do JSONB do quadro + incremento de ``versao_otimista``."""
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _update() -> Any:
            q: Any = (
                self._client.table("diagnosticos")
                .update(
                    {
                        "quadro_implantacao_anotacoes": quadro_implantacao_anotacoes,
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

    async def atualizar_painel_estado_ciclo_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        painel_estado_ciclo: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _update() -> Any:
            q: Any = (
                self._client.table("diagnosticos")
                .update(
                    {
                        "painel_estado_ciclo": painel_estado_ciclo,
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

    async def atualizar_explicacao_score_llm(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        snapshot: dict[str, Any],
    ) -> None:
        sid, stid = str(diagnostico_id), str(tenant_id)

        def _update() -> Any:
            return (
                self._client.table("diagnosticos")
                .update({"explicacao_score_llm": snapshot})
                .eq("id", sid)
                .eq("tenant_id", stid)
                .execute()
            )

        response = await asyncio.to_thread(_update)
        if not response.data:
            raise ValueError("Diagnóstico não encontrado para persistir explicação LLM")

    async def registrar_explicacao_score_llm_historico(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        snapshot: dict[str, Any],
        *,
        actor_user_id: UUID | None,
        trace_id: str | None,
    ) -> None:
        _ = actor_user_id
        chave = (str(tenant_id), str(diagnostico_id))
        item = dict(snapshot)
        if trace_id:
            item["trace_id"] = trace_id
        self._explicacao_historico_mem.setdefault(chave, []).insert(0, item)

    async def listar_explicacao_score_llm_historico(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        return list(
            self._explicacao_historico_mem.get((str(tenant_id), str(diagnostico_id)), [])[:limit]
        )

    def _salvar_e_materializar_thread(
        self, diagnostico: Diagnostico, score_completo: ScoreCompleto
    ) -> PlanoPainelSerializado:
        payload = self._para_dict(diagnostico)
        self._client.table("diagnosticos").upsert(payload).execute()
        return materializar_plano_painel_supabase(self._client, diagnostico, score_completo)

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
        return await asyncio.to_thread(
            self._salvar_e_materializar_thread, diagnostico, score_completo
        )

    async def buscar_plano_painel_serializado(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        return await asyncio.to_thread(
            buscar_plano_painel_serializado_supabase, self._client, diagnostico_id, tenant_id
        )

    def _materializar_backfill_thread(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        sid, tid = str(diagnostico_id), str(tenant_id)
        chk = (
            self._client.table("diagnostico_plano_acao")
            .select("id")
            .eq("diagnostico_id", sid)
            .eq("tenant_id", tid)
            .eq("versao_plano", 1)
            .limit(1)
            .execute()
        )
        if chk.data:
            return None
        d_resp = (
            self._client.table("diagnosticos")
            .select("*")
            .eq("id", sid)
            .eq("tenant_id", tid)
            .single()
            .execute()
        )
        row_raw = d_resp.data
        if not isinstance(row_raw, dict):
            return None
        row = cast("dict[str, Any]", row_raw)
        if row.get("status") != StatusDiagnostico.FINALIZADO.value:
            return None
        sc_raw = row.get("score_completo")
        if not isinstance(sc_raw, dict):
            return None
        try:
            sc = ScoreCompleto.desde_dict(sc_raw)
        except (KeyError, TypeError, ValueError):
            return None
        d = self._para_entity(row)
        return materializar_plano_painel_supabase(self._client, d, sc)

    async def materializar_plano_painel_idempotente_backfill(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        return await asyncio.to_thread(
            self._materializar_backfill_thread, diagnostico_id, tenant_id
        )

    async def inserir_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        titulo: str,
        ordem: int = 0,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            inserir_subtarefa_supabase,
            self._client,
            tenant_id,
            diagnostico_id,
            plano_acao_id,
            titulo,
            ordem,
        )

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
        return await asyncio.to_thread(
            atualizar_subtarefa_supabase,
            self._client,
            tenant_id,
            diagnostico_id,
            subtarefa_id,
            titulo=titulo,
            status=status,
            prazo=prazo,
            comentarios=comentarios,
            ordem=ordem,
        )

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
            "respondente_ip_origem": d.respondente.ip_origem if d.respondente else None,
            "empresa_cnpj": d.empresa.cnpj,
            "empresa_razao_social": d.empresa.razao_social,
            "empresa_porte": d.empresa.porte.value,
            "empresa_regime": d.empresa.regime.value,
            "empresa_cnae": d.empresa.cnae_principal,
            "empresa_uf": d.empresa.uf,
            "empresa_setor_macro": d.empresa.setor_macro.value,
            "empresa_faixa_faturamento": (
                d.empresa.faixa_faturamento.value
                if d.empresa.faixa_faturamento is not None
                else None
            ),
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
            "quadro_implantacao_anotacoes": getattr(d, "quadro_implantacao_anotacoes", None),
            "aceite_termos_privacidade_em": (
                d.aceite_termos_privacidade_em.isoformat()
                if d.aceite_termos_privacidade_em is not None
                else None
            ),
            "locale_relatorio": getattr(d, "locale_relatorio", "pt-BR"),
            "versao_plano": int(getattr(d, "versao_plano", 1) or 1),
            "explicacao_score_llm": getattr(d, "explicacao_score_llm", None),
            "painel_estado_ciclo": getattr(
                d,
                "painel_estado_ciclo",
                PainelEstadoCicloDiagnostico.EM_ANDAMENTO.value,
            ),
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
        checklist_m12 = normalizar_checklist_m12_estado_bruto(m12_raw)

        aceite_raw = row.get("aceite_termos_privacidade_em")
        aceite_em: datetime | None = None
        if aceite_raw is not None:
            aceite_em = datetime.fromisoformat(str(aceite_raw).replace("Z", "+00:00"))

        loc_raw = row.get("locale_relatorio") or "pt-BR"
        locale_relatorio = str(loc_raw).strip() if loc_raw is not None else "pt-BR"

        ff_raw = row.get("empresa_faixa_faturamento")
        faixa: FaixaFaturamentoDeclarada | None = None
        if ff_raw is not None and str(ff_raw).strip() != "":
            try:
                faixa = FaixaFaturamentoDeclarada(str(ff_raw).strip())
            except ValueError:
                faixa = None

        quadro_raw = row.get("quadro_implantacao_anotacoes")
        quadro: dict[str, dict[str, str | list[str]]] | None = None
        if isinstance(quadro_raw, dict):
            tmp: dict[str, dict[str, str | list[str]]] = {}
            for k, v in quadro_raw.items():
                if isinstance(v, dict):
                    prazo = str(v.get("prazo_meta", "") or "").strip()
                    comentarios: list[str] = []
                    cr = v.get("comentarios")
                    if isinstance(cr, list):
                        comentarios = [str(x).strip() for x in cr if str(x).strip()]
                    if not comentarios:
                        leg = str(v.get("comentario", "") or "").strip()
                        if leg:
                            comentarios = [leg]
                    item_sq: dict[str, str | list[str]] = {
                        "prazo_meta": prazo,
                        "comentarios": comentarios,
                    }
                    dp_sq = str(v.get("descricao_personalizada", "") or "").strip()
                    if dp_sq:
                        item_sq["descricao_personalizada"] = dp_sq
                    tmp[str(k)] = item_sq
            quadro = tmp if tmp else None

        expl_raw = row.get("explicacao_score_llm")
        explicacao_score_llm = expl_raw if isinstance(expl_raw, dict) else None

        raw_pec = row.get("painel_estado_ciclo")
        if isinstance(raw_pec, str) and raw_pec.strip():
            pec = raw_pec.strip()
        elif str(row.get("status")) == StatusDiagnostico.FINALIZADO.value:
            pec = PainelEstadoCicloDiagnostico.REALIZADO.value
        else:
            pec = PainelEstadoCicloDiagnostico.EM_ANDAMENTO.value

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
                faixa_faturamento=faixa,
            ),
            respondente=Respondente(
                email=email_resp,
                nome=row.get("respondente_nome"),
                cargo=row.get("respondente_cargo"),
                telefone=row.get("respondente_telefone"),
                ip_origem=row.get("respondente_ip_origem"),
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
            quadro_implantacao_anotacoes=quadro,
            aceite_termos_privacidade_em=aceite_em,
            locale_relatorio=locale_relatorio,
            versao_plano=int(row.get("versao_plano") or 1),
            explicacao_score_llm=explicacao_score_llm,
            numero_interno_grupo=(
                int(raw_nim) if (raw_nim := row.get("numero_interno_grupo")) is not None else None
            ),
            painel_estado_ciclo=pec,
        )
