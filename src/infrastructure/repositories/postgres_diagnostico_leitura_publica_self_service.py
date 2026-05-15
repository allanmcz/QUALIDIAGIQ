"""
Token de leitura pública após conclusão self-service (PostgreSQL síncrono).

Camada: Infrastructure — invocado via asyncio.to_thread a partir das rotas.
Analogia: «chave de consulta» de um recibo: não é login, só prova que quem concluiu OTP pode ver o snapshot.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

import psycopg2
from psycopg2.extras import RealDictCursor

if TYPE_CHECKING:
    import uuid

_LEITURA_TTL_DIAS = 7


def _token_sha256(token_plain: str) -> str:
    return hashlib.sha256(token_plain.encode("utf-8")).hexdigest()


def inserir_leitura_publica_self_service_sync(
    dsn: str, diagnostico_id: uuid.UUID, tenant_id: uuid.UUID
) -> str:
    """
    Regista token de leitura; devolve o valor em texto claro uma única vez (para a resposta HTTP).
    """
    token_plain = secrets.token_urlsafe(32)
    th = _token_sha256(token_plain)
    expira = datetime.now(UTC) + timedelta(days=_LEITURA_TTL_DIAS)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO diagnostico_leitura_publica_self_service (
                    diagnostico_id, tenant_id, token_sha256, expira_em
                ) VALUES (%s, %s, %s, %s)
                """,
                (str(diagnostico_id), str(tenant_id), th, expira),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return token_plain


def buscar_diagnostico_conclusao_publica_sync(
    dsn: str,
    *,
    diagnostico_id: uuid.UUID,
    tenant_id_esperado: uuid.UUID,
    token_plain: str,
) -> dict[str, Any] | None:
    """
    Valida token + par (diagnostico_id, tenant) e devolve linha de ``diagnosticos`` ou None.
    """
    th = _token_sha256(token_plain.strip())
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 1
                FROM diagnostico_leitura_publica_self_service dl
                WHERE dl.token_sha256 = %s
                  AND dl.diagnostico_id = %s
                  AND dl.tenant_id = %s
                  AND dl.expira_em > CURRENT_TIMESTAMP
                LIMIT 1
                """,
                (th, str(diagnostico_id), str(tenant_id_esperado)),
            )
            if cur.fetchone() is None:
                return None
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, status, empresa_razao_social, locale_relatorio, score_completo,
                       explicacao_score_llm
                FROM diagnosticos
                WHERE id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (str(diagnostico_id), str(tenant_id_esperado)),
            )
            drow = cur.fetchone()
        if not drow:
            return None
        return cast("dict[str, Any]", dict(drow))
    finally:
        conn.close()
