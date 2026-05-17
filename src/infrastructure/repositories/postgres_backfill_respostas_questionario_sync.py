"""
Backfill de ``diagnostico_resposta_questionario`` a partir de rascunhos consumidos.

Camada: Infrastructure
"""

from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID  # noqa: TC003

import psycopg2
from psycopg2.extras import RealDictCursor

from src.infrastructure.repositories.postgres_diagnostico_resposta_sync import (
    inserir_respostas_questionario_em_cursor,
    respostas_questionario_existem_sync,
)


def listar_diagnosticos_sem_respostas_sync(
    dsn: str,
    tenant_id: UUID,
    *,
    limite: int = 100,
) -> list[dict[str, Any]]:
    """Diagnósticos finalizados do tenant sem linhas em ``diagnostico_resposta_questionario``."""
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT d.id, d.tenant_id, d.empresa_cnpj, d.respondente_email, d.finalizado_em
                FROM diagnosticos d
                WHERE d.tenant_id = %s
                  AND d.status = 'finalizado'
                  AND NOT EXISTS (
                      SELECT 1 FROM diagnostico_resposta_questionario drq
                      WHERE drq.diagnostico_id = d.id
                  )
                ORDER BY d.finalizado_em DESC NULLS LAST
                LIMIT %s
                """,
                (str(tenant_id), limite),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def buscar_payload_rascunho_para_backfill_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    *,
    janela_horas: int = 48,
) -> dict[str, Any] | None:
    """
    Tenta localizar rascunho self-service consumido com mesmo e-mail/CNPJ e horário próximo.

    Fonte: ``diagnostico_rascunhos_self_service.payload_json`` (corpo do POST antes do OTP).
    """
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.payload_json, r.consumido_em
                FROM diagnosticos d
                JOIN diagnostico_rascunhos_self_service r
                  ON lower(trim(d.respondente_email)) = r.email_norm
                WHERE d.id = %s
                  AND d.tenant_id = %s
                  AND r.consumido_em IS NOT NULL
                  AND d.finalizado_em IS NOT NULL
                  AND r.consumido_em BETWEEN
                      d.finalizado_em - make_interval(hours => %s)
                      AND d.finalizado_em + make_interval(hours => %s)
                ORDER BY abs(extract(epoch FROM (r.consumido_em - d.finalizado_em)))
                LIMIT 20
                """,
                (str(diagnostico_id), str(tenant_id), janela_horas, janela_horas),
            )
            candidatos = cur.fetchall()
        if not candidatos:
            return None
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT empresa_cnpj FROM diagnosticos WHERE id = %s",
                (str(diagnostico_id),),
            )
            row_d = cur.fetchone()
        if not row_d:
            return None
        cnpj_diag = "".join(ch for ch in str(row_d["empresa_cnpj"] or "") if ch.isdigit())
        for r in candidatos:
            pj = r["payload_json"]
            if isinstance(pj, str):
                pj = json.loads(pj)
            if not isinstance(pj, dict):
                continue
            emp = pj.get("empresa")
            if not isinstance(emp, dict):
                continue
            cnpj_payload = "".join(ch for ch in str(emp.get("cnpj", "") or "") if ch.isdigit())
            if cnpj_diag and cnpj_payload and cnpj_diag != cnpj_payload:
                continue
            return cast("dict[str, Any]", pj)
        return None
    finally:
        conn.close()


def persistir_linhas_backfill_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    linhas: tuple[Any, ...],
) -> bool:
    """Insere linhas se ainda não existirem (idempotente). Retorna True se inseriu."""
    if respostas_questionario_existem_sync(dsn, diagnostico_id, tenant_id):
        return False
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            inserir_respostas_questionario_em_cursor(cur, diagnostico_id, tenant_id, linhas)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
