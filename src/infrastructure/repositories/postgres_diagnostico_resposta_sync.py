"""
Persistência e leitura de ``diagnostico_resposta_questionario`` (psycopg2).

Camada: Infrastructure
"""

from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID

from psycopg2.extras import Json, RealDictCursor

from src.domain.value_objects.linha_resposta_questionario import LinhaRespostaQuestionario


def inserir_respostas_questionario_em_cursor(
    cur: Any,
    diagnostico_id: UUID,
    tenant_id: UUID,
    linhas: tuple[LinhaRespostaQuestionario, ...],
) -> None:
    """INSERT em lote na mesma transação do diagnóstico (append-only)."""
    if not linhas:
        return
    did, tid = str(diagnostico_id), str(tenant_id)
    for ln in linhas:
        cur.execute(
            """
            INSERT INTO diagnostico_resposta_questionario (
                diagnostico_id, tenant_id, ordem_exibicao,
                pergunta_id, pergunta_codigo, dimensao, tipo_pergunta,
                texto_pergunta, peso, base_legal, pilar_abnt,
                valor_bruto, valor_exibicao, pontuacao_item, excluida_calculo
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                did,
                tid,
                ln.ordem_exibicao,
                str(ln.pergunta_id),
                ln.pergunta_codigo,
                ln.dimensao,
                ln.tipo_pergunta,
                ln.texto_pergunta,
                ln.peso,
                ln.base_legal,
                ln.pilar_abnt,
                Json(_valor_bruto_json(ln.valor_bruto)),
                ln.valor_exibicao,
                ln.pontuacao_item,
                ln.excluida_calculo,
            ),
        )


def _valor_bruto_json(valor: Any) -> Any:
    """Garante tipo serializável em JSONB."""
    if isinstance(valor, (str, int, float, bool)) or valor is None:
        return valor
    if isinstance(valor, list):
        return valor
    return json.loads(json.dumps(valor, ensure_ascii=False))


def listar_respostas_questionario_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
) -> list[dict[str, Any]]:
    """Lista respostas ordenadas por ``ordem_exibicao``."""
    import psycopg2

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    ordem_exibicao,
                    pergunta_id,
                    pergunta_codigo,
                    dimensao,
                    tipo_pergunta,
                    texto_pergunta,
                    peso,
                    base_legal,
                    pilar_abnt,
                    valor_bruto,
                    valor_exibicao,
                    pontuacao_item,
                    excluida_calculo,
                    criado_em
                FROM diagnostico_resposta_questionario
                WHERE diagnostico_id = %s AND tenant_id = %s
                ORDER BY ordem_exibicao ASC
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            rows = cur.fetchall()
        return [_row_http(cast("dict[str, Any]", dict(r))) for r in rows]
    finally:
        conn.close()


def respostas_questionario_existem_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
) -> bool:
    import psycopg2

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM diagnostico_resposta_questionario
                WHERE diagnostico_id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def _row_http(row: dict[str, Any]) -> dict[str, Any]:
    pid = row.get("pergunta_id")
    ce = row.get("criado_em")
    return {
        "ordem_exibicao": int(row["ordem_exibicao"]),
        "pergunta_id": str(pid) if pid is not None else "",
        "pergunta_codigo": str(row["pergunta_codigo"]),
        "dimensao": str(row["dimensao"]),
        "tipo_pergunta": str(row["tipo_pergunta"]),
        "texto_pergunta": str(row["texto_pergunta"]),
        "peso": float(row["peso"]),
        "base_legal": row.get("base_legal"),
        "pilar_abnt": row.get("pilar_abnt"),
        "valor_bruto": row.get("valor_bruto"),
        "valor_exibicao": str(row["valor_exibicao"]),
        "pontuacao_item": (
            float(row["pontuacao_item"]) if row.get("pontuacao_item") is not None else None
        ),
        "excluida_calculo": bool(row.get("excluida_calculo")),
        "criado_em": ce.isoformat() if ce is not None else None,
    }
