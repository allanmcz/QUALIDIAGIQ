"""
Materialização de respostas do questionário via PostgREST (Supabase).

Camada: Infrastructure
"""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from src.domain.value_objects.linha_resposta_questionario import LinhaRespostaQuestionario


def inserir_respostas_questionario_supabase(
    client: Any,
    diagnostico_id: UUID,
    tenant_id: UUID,
    linhas: tuple[LinhaRespostaQuestionario, ...],
    *,
    refazer_lote: int = 1,
) -> None:
    if not linhas:
        return
    rows = [_linha_para_row(diagnostico_id, tenant_id, ln, refazer_lote=refazer_lote) for ln in linhas]
    client.table("diagnostico_resposta_questionario").insert(rows).execute()


def listar_respostas_questionario_supabase(
    client: Any,
    diagnostico_id: UUID,
    tenant_id: UUID,
) -> list[dict[str, Any]]:
    res = (
        client.table("diagnostico_resposta_questionario")
        .select(
            "ordem_exibicao, pergunta_id, pergunta_codigo, dimensao, tipo_pergunta, "
            "texto_pergunta, peso, base_legal, pilar_abnt, valor_bruto, valor_exibicao, "
            "pontuacao_item, excluida_calculo, criado_em, refazer_lote"
        )
        .eq("diagnostico_id", str(diagnostico_id))
        .eq("tenant_id", str(tenant_id))
        .order("ordem_exibicao")
        .execute()
    )
    por_codigo: dict[str, dict[str, Any]] = {}
    for row in res.data or []:
        pid = row.get("pergunta_id")
        ce = row.get("criado_em")
        codigo = str(row["pergunta_codigo"])
        lote = int(row.get("refazer_lote") or 1)
        item = {
            "ordem_exibicao": int(row["ordem_exibicao"]),
            "pergunta_id": str(pid) if pid is not None else "",
            "pergunta_codigo": codigo,
            "dimensao": str(row["dimensao"]),
            "tipo_pergunta": str(row["tipo_pergunta"]),
            "texto_pergunta": str(row["texto_pergunta"]),
            "peso": float(row["peso"]),
            "base_legal": row.get("base_legal"),
            "pilar_abnt": row.get("pilar_abnt"),
            "valor_bruto": row.get("valor_bruto"),
            "valor_exibicao": str(row["valor_exibicao"]),
            "pontuacao_item": (
                float(row["pontuacao_item"])
                if row.get("pontuacao_item") is not None
                else None
            ),
            "excluida_calculo": bool(row.get("excluida_calculo")),
            "criado_em": ce,
            "refazer_lote": lote,
        }
        prev = por_codigo.get(codigo)
        if prev is None or int(prev.get("refazer_lote") or 1) < lote:
            por_codigo[codigo] = item
    return sorted(por_codigo.values(), key=lambda x: int(x["ordem_exibicao"]))


def _linha_para_row(
    diagnostico_id: UUID,
    tenant_id: UUID,
    ln: LinhaRespostaQuestionario,
    *,
    refazer_lote: int = 1,
) -> dict[str, Any]:
    vb = ln.valor_bruto
    if not isinstance(vb, (str, int, float, bool, list, dict)) and vb is not None:
        vb = json.loads(json.dumps(vb, ensure_ascii=False))
    return {
        "diagnostico_id": str(diagnostico_id),
        "tenant_id": str(tenant_id),
        "refazer_lote": int(refazer_lote),
        "ordem_exibicao": ln.ordem_exibicao,
        "pergunta_id": str(ln.pergunta_id),
        "pergunta_codigo": ln.pergunta_codigo,
        "dimensao": ln.dimensao,
        "tipo_pergunta": ln.tipo_pergunta,
        "texto_pergunta": ln.texto_pergunta,
        "peso": ln.peso,
        "base_legal": ln.base_legal,
        "pilar_abnt": ln.pilar_abnt,
        "valor_bruto": vb,
        "valor_exibicao": ln.valor_exibicao,
        "pontuacao_item": ln.pontuacao_item,
        "excluida_calculo": ln.excluida_calculo,
    }
