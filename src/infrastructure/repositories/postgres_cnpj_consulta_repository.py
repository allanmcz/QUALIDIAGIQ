"""
Persistência de ``cnpj_consultas`` e merge empresa em diagnóstico ``em_andamento``.

Camada: Infrastructure (psycopg2 síncrono — chamado via ``asyncio.to_thread`` na API).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.application.ports.cnpj_consulta_repository_port import CnpjConsultaRepositoryPort
from src.domain.entities.diagnostico import EmpresaInfo


class PostgresCnpjConsultaRepository(CnpjConsultaRepositoryPort):
    """Implementação SQL direto — exige ``DATABASE_URL`` sync no serviço."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    def buscar_por_idempotencia(
        self, tenant_id: UUID, idempotency_key: str
    ) -> dict[str, Any] | None:
        conn = psycopg2.connect(self._dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM cnpj_consultas
                    WHERE tenant_id = %s AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (str(tenant_id), idempotency_key.strip()[:128]),
                )
                row = cur.fetchone()
            return cast("dict[str, Any]", dict(row)) if row else None
        finally:
            conn.close()

    def buscar_ultimo_cache_valido_triplo_ttl(
        self, tenant_id: UUID, cnpj: str
    ) -> dict[str, Any] | None:
        conn = psycopg2.connect(self._dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM cnpj_consultas
                    WHERE tenant_id = %s
                      AND cnpj = %s
                      AND expira_cadastral_at > NOW()
                      AND expira_qualificacao_at > NOW()
                      AND expira_situacao_at > NOW()
                    ORDER BY consultado_em DESC
                    LIMIT 1
                    """,
                    (str(tenant_id), cnpj),
                )
                row = cur.fetchone()
            return cast("dict[str, Any]", dict(row)) if row else None
        finally:
            conn.close()

    def inserir_consulta(
        self,
        *,
        tenant_id: UUID,
        idempotency_key: str,
        cnpj: str,
        diagnostico_id: UUID | None,
        payload_bruto: dict[str, Any],
        payload_canonico: dict[str, Any],
        payload_hash: str,
        fonte: str,
        consultado_em: datetime,
        expira_cadastral_at: datetime,
        expira_qualificacao_at: datetime,
        expira_situacao_at: datetime,
        latencia_ms: int | None,
        http_status: int | None,
        trace_id: str | None,
    ) -> UUID:
        if consultado_em.tzinfo is None:
            consultado_em = consultado_em.replace(tzinfo=UTC)
        conn = psycopg2.connect(self._dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cnpj_consultas (
                        tenant_id, idempotency_key, cnpj, diagnostico_id,
                        payload_bruto, payload_canonico, payload_hash, fonte,
                        consultado_em,
                        expira_cadastral_at, expira_qualificacao_at, expira_situacao_at,
                        latencia_ms, http_status, trace_id
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s,
                        %s, %s, %s,
                        %s, %s, %s
                    )
                    RETURNING id
                    """,
                    (
                        str(tenant_id),
                        idempotency_key.strip()[:128],
                        cnpj,
                        str(diagnostico_id) if diagnostico_id else None,
                        Json(payload_bruto),
                        Json(payload_canonico),
                        payload_hash,
                        fonte,
                        consultado_em,
                        expira_cadastral_at,
                        expira_qualificacao_at,
                        expira_situacao_at,
                        latencia_ms,
                        http_status,
                        (trace_id or "")[:128] or None,
                    ),
                )
                raw_id = cur.fetchone()
            conn.commit()
            if not raw_id:
                raise RuntimeError("INSERT cnpj_consultas não retornou id.")
            return UUID(str(raw_id[0]))
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def atualizar_empresa_diagnostico_em_andamento(
        self,
        *,
        tenant_id: UUID,
        diagnostico_id: UUID,
        nova_empresa: EmpresaInfo,
        historico: list[tuple[str, str | None, str]],
        cnpj_consulta_id: UUID | None,
    ) -> None:
        conn = psycopg2.connect(self._dsn)
        try:
            conn.autocommit = False
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT status FROM diagnosticos
                    WHERE id = %s AND tenant_id = %s
                    FOR UPDATE
                    """,
                    (str(diagnostico_id), str(tenant_id)),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError("Diagnóstico não encontrado para o tenant.")
                if str(row["status"]) != "em_andamento":
                    raise ValueError(
                        "Só é permitido aplicar consulta CNPJ em diagnóstico em_andamento "
                        "(evidência finalizada é imutável — WORM)."
                    )
                cur.execute(
                    """
                    UPDATE diagnosticos SET
                        empresa_cnpj = %s,
                        empresa_razao_social = %s,
                        empresa_porte = %s,
                        empresa_regime = %s,
                        empresa_cnae = %s,
                        empresa_uf = %s,
                        empresa_setor_macro = %s
                    WHERE id = %s AND tenant_id = %s AND status = 'em_andamento'
                    """,
                    (
                        nova_empresa.cnpj,
                        nova_empresa.razao_social,
                        nova_empresa.porte.value,
                        nova_empresa.regime.value,
                        nova_empresa.cnae_principal,
                        nova_empresa.uf,
                        nova_empresa.setor_macro.value,
                        str(diagnostico_id),
                        str(tenant_id),
                    ),
                )
                if cur.rowcount != 1:
                    raise ValueError("Não foi possível atualizar empresa do diagnóstico.")
                cid = str(cnpj_consulta_id) if cnpj_consulta_id else None
                for campo, anterior, novo in historico:
                    cur.execute(
                        """
                        INSERT INTO diagnostico_empresa_campo_historico (
                            tenant_id, diagnostico_id, cnpj_consulta_id,
                            campo, valor_anterior, valor_novo
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(tenant_id),
                            str(diagnostico_id),
                            cid,
                            campo,
                            anterior,
                            novo,
                        ),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
