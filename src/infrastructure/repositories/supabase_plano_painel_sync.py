"""
Materialização e leitura do plano via PostgREST (cliente Supabase síncrono).

Camada: Infrastructure — sem ``DATABASE_URL`` directo; respeita RLS do JWT do ``client``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any, cast

from src.application.services.plano_painel_derivacao import derivar_plano_painel_materializado
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import ScoreCompleto


def _del_tabela_versao(
    client: Any, tabela: str, diagnostico_id: str, tenant_id: str, versao_plano: int
) -> None:
    client.table(tabela).delete().eq("diagnostico_id", diagnostico_id).eq(
        "tenant_id", tenant_id
    ).eq("versao_plano", versao_plano).execute()


def materializar_plano_painel_supabase(
    client: Any, diagnostico: Diagnostico, score_completo: ScoreCompleto
) -> PlanoPainelSerializado:
    """Remove linhas da versão e reinsere (melhor esforço sem transação explícita no PostgREST)."""
    sid, tid = str(diagnostico.id), str(diagnostico.tenant_id)
    vp = int(getattr(diagnostico, "versao_plano", 1) or 1)
    deriv = derivar_plano_painel_materializado(diagnostico, score_completo, versao_plano=vp)
    _del_tabela_versao(client, "diagnostico_plano_matriz", sid, tid, vp)
    _del_tabela_versao(client, "diagnostico_plano_cronograma", sid, tid, vp)
    _del_tabela_versao(client, "diagnostico_plano_acao", sid, tid, vp)

    for ln in deriv.linhas_acao:
        client.table("diagnostico_plano_acao").insert(
            {
                "id": str(ln.id),
                "diagnostico_id": sid,
                "tenant_id": tid,
                "versao_plano": vp,
                "ordem_exibicao": ln.ordem_exibicao,
                "frente_indice": ln.frente_indice,
                "acao_indice": ln.acao_indice,
                "frente_nome": ln.frente_nome,
                "texto_acao": ln.texto_acao,
                "responsavel_sugerido": ln.responsavel_sugerido,
                "prazo_sugerido_texto": ln.prazo_sugerido_texto,
                "criticidade": ln.criticidade,
                "base_legal": ln.base_legal,
                "origem_motor": ln.origem_motor,
                "prioridade_motor": ln.prioridade_motor,
            }
        ).execute()
    for m in deriv.linhas_matriz:
        client.table("diagnostico_plano_matriz").insert(
            {
                "id": str(m.id),
                "diagnostico_id": sid,
                "tenant_id": tid,
                "versao_plano": vp,
                "ordem_exibicao": m.ordem_exibicao,
                "departamento": m.departamento,
                "impacto_resumo": m.impacto_resumo,
                "criticidade": m.criticidade,
                "base_legal": m.base_legal,
            }
        ).execute()
    for c in deriv.linhas_cronograma:
        client.table("diagnostico_plano_cronograma").insert(
            {
                "id": str(c.id),
                "diagnostico_id": sid,
                "tenant_id": tid,
                "versao_plano": vp,
                "ordem_exibicao": c.ordem_exibicao,
                "fase": c.fase,
                "foco": c.foco,
                "referencia_normativa": c.referencia_normativa,
            }
        ).execute()
    out = buscar_plano_painel_serializado_supabase(client, diagnostico.id, diagnostico.tenant_id)
    return out if out is not None else deriv.serializado_http


def buscar_plano_painel_serializado_supabase(
    client: Any, diagnostico_id: Any, tenant_id: Any
) -> PlanoPainelSerializado | None:
    sid, tid = str(diagnostico_id), str(tenant_id)
    ac_resp = (
        client.table("diagnostico_plano_acao")
        .select("*")
        .eq("diagnostico_id", sid)
        .eq("tenant_id", tid)
        .order("ordem_exibicao")
        .execute()
    )
    acoes = ac_resp.data or []
    if not acoes:
        return None
    versao_plano = int(acoes[0]["versao_plano"])
    mat_resp = (
        client.table("diagnostico_plano_matriz")
        .select("*")
        .eq("diagnostico_id", sid)
        .eq("tenant_id", tid)
        .eq("versao_plano", versao_plano)
        .order("ordem_exibicao")
        .execute()
    )
    mat_rows = mat_resp.data or []
    cro_resp = (
        client.table("diagnostico_plano_cronograma")
        .select("*")
        .eq("diagnostico_id", sid)
        .eq("tenant_id", tid)
        .eq("versao_plano", versao_plano)
        .order("ordem_exibicao")
        .execute()
    )
    cro_rows = cro_resp.data or []
    sub_resp = (
        client.table("diagnostico_plano_subtarefa")
        .select("*")
        .eq("diagnostico_id", sid)
        .eq("tenant_id", tid)
        .execute()
    )
    sub_rows = sub_resp.data or []

    por_fi: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in acoes:
        por_fi[int(r["frente_indice"])].append(cast("dict[str, Any]", r))

    checklist: list[dict[str, Any]] = []
    for fi in sorted(por_fi.keys()):
        rows_f = sorted(por_fi[fi], key=lambda x: int(x["ordem_exibicao"]))
        nome_f = str(rows_f[0]["frente_nome"])
        acoes_http: list[dict[str, Any]] = []
        for r in rows_f:
            pid = str(r["id"])
            st_list = [
                _sub_http(cast("dict[str, Any]", sr))
                for sr in sub_rows
                if str(sr["plano_acao_id"]) == pid
            ]
            acoes_http.append(
                {
                    "descricao": r["texto_acao"],
                    "responsavel": r["responsavel_sugerido"],
                    "prazo": r["prazo_sugerido_texto"],
                    "criticidade": r["criticidade"],
                    "base_legal": r.get("base_legal"),
                    "prioridade": int(r["prioridade_motor"]),
                    "plano_acao_id": pid,
                    "chave_quadro_legado": f"f{int(r['frente_indice'])}_a{int(r['acao_indice'])}",
                    "subtarefas": st_list,
                }
            )
        checklist.append({"nome": nome_f, "acoes": acoes_http})

    matriz_http = [
        {
            "departamento": mr["departamento"],
            "impacto_resumo": mr["impacto_resumo"],
            "criticidade": mr["criticidade"],
            "base_legal": mr.get("base_legal"),
        }
        for mr in mat_rows
    ]
    cron_http = [
        {
            "fase": cr["fase"],
            "foco": cr["foco"],
            "referencia_normativa": cr["referencia_normativa"],
        }
        for cr in cro_rows
    ]
    sub_map: dict[str, tuple[dict[str, Any], ...]] = {}
    for sr in sub_rows:
        pid = str(sr["plano_acao_id"])
        sub_map[pid] = (*sub_map.get(pid, ()), _sub_http(cast("dict[str, Any]", sr)))
    return PlanoPainelSerializado(
        versao_plano=versao_plano,
        checklist=tuple(checklist),
        matriz_impacto=tuple(matriz_http),
        cronograma=tuple(cron_http),
        subtarefas_por_acao=sub_map,
    )


def _sub_http(r: dict[str, Any]) -> dict[str, Any]:
    prazo = r.get("prazo")
    if prazo is None:
        prazo_out = None
    elif isinstance(prazo, str):
        prazo_out = prazo[:10]
    elif isinstance(prazo, datetime):
        prazo_out = prazo.date().isoformat()
    else:
        prazo_out = str(prazo)[:10]
    return {
        "id": str(r["id"]),
        "titulo": r["titulo"],
        "status": r["status"],
        "prazo": prazo_out,
        "comentarios": r.get("comentarios"),
        "ordem": int(r["ordem"]),
    }


def inserir_subtarefa_supabase(
    client: Any, tenant_id: Any, diagnostico_id: Any, plano_acao_id: Any, titulo: str, ordem: int
) -> dict[str, Any]:
    sid, tid, aid = str(diagnostico_id), str(tenant_id), str(plano_acao_id)
    chk = (
        client.table("diagnostico_plano_acao")
        .select("id")
        .eq("id", aid)
        .eq("diagnostico_id", sid)
        .eq("tenant_id", tid)
        .limit(1)
        .execute()
    )
    if not chk.data:
        raise ValueError("Ação do plano inexistente ou fora do tenant/diagnóstico.")
    ins = (
        client.table("diagnostico_plano_subtarefa")
        .insert(
            {
                "plano_acao_id": aid,
                "diagnostico_id": sid,
                "tenant_id": tid,
                "titulo": titulo.strip(),
                "ordem": ordem,
            }
        )
        .execute()
    )
    data = ins.data or []
    if not data:
        raise RuntimeError("Falha ao inserir subtarefa (PostgREST sem linha retornada).")
    return _sub_http(cast("dict[str, Any]", data[0]))


def atualizar_subtarefa_supabase(
    client: Any,
    tenant_id: Any,
    diagnostico_id: Any,
    subtarefa_id: Any,
    *,
    titulo: str | None,
    status: str | None,
    prazo: date | None,
    comentarios: str | None,
    ordem: int | None,
) -> dict[str, Any] | None:
    sid, tid, sub_id = str(diagnostico_id), str(tenant_id), str(subtarefa_id)
    patch: dict[str, Any] = {}
    if titulo is not None:
        patch["titulo"] = titulo.strip()
    if status is not None:
        patch["status"] = status.strip()
    if prazo is not None:
        patch["prazo"] = prazo.isoformat()
    if comentarios is not None:
        patch["comentarios"] = comentarios
    if ordem is not None:
        patch["ordem"] = ordem
    if not patch:
        r = (
            client.table("diagnostico_plano_subtarefa")
            .select("*")
            .eq("id", sub_id)
            .eq("tenant_id", tid)
            .eq("diagnostico_id", sid)
            .limit(1)
            .execute()
        )
        row = r.data[0] if r.data else None
        return _sub_http(cast("dict[str, Any]", row)) if row else None
    patch["atualizado_em"] = datetime.now(UTC).isoformat()
    up = (
        client.table("diagnostico_plano_subtarefa")
        .update(patch)
        .eq("id", sub_id)
        .eq("tenant_id", tid)
        .eq("diagnostico_id", sid)
        .select("*")
        .limit(1)
        .execute()
    )
    row2 = up.data[0] if up.data else None
    return _sub_http(cast("dict[str, Any]", row2)) if row2 else None
