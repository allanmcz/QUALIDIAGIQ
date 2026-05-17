"""
Persistência sync de ``empresa_painel_arquivo``.

Camada: Infrastructure
"""

from __future__ import annotations

from uuid import UUID

from src.infrastructure.repositories.postgres_empresa_painel_arquivo_compat import (
    erro_tabela_empresa_painel_arquivo_ausente,
)


class EmpresaPainelArquivoTabelaAusenteError(RuntimeError):
    """Migration 0053 não aplicada — arquivo de empresa indisponível."""


def definir_arquivado_sync(
    dsn: str,
    tenant_id: UUID,
    empresa_cnpj: str,
    *,
    arquivado: bool,
    actor_user_id: UUID | None,
) -> bool:
    import psycopg2

    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            if arquivado:
                cur.execute(
                    """
                    INSERT INTO empresa_painel_arquivo (tenant_id, empresa_cnpj, arquivado_por_user_id)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tenant_id, empresa_cnpj) DO NOTHING
                    """,
                    (str(tenant_id), empresa_cnpj, str(actor_user_id) if actor_user_id else None),
                )
                mudou = cur.rowcount == 1
            else:
                cur.execute(
                    """
                    DELETE FROM empresa_painel_arquivo
                    WHERE tenant_id = %s AND empresa_cnpj = %s
                    """,
                    (str(tenant_id), empresa_cnpj),
                )
                mudou = cur.rowcount == 1
        conn.commit()
        return mudou
    except Exception as exc:
        conn.rollback()
        if erro_tabela_empresa_painel_arquivo_ausente(exc):
            raise EmpresaPainelArquivoTabelaAusenteError(
                "Tabela empresa_painel_arquivo ausente — execute make migrate (0053)."
            ) from exc
        raise
    finally:
        conn.close()


def esta_arquivada_sync(dsn: str, tenant_id: UUID, empresa_cnpj: str) -> bool:
    import psycopg2

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT 1 FROM empresa_painel_arquivo
                    WHERE tenant_id = %s AND empresa_cnpj = %s
                    LIMIT 1
                    """,
                    (str(tenant_id), empresa_cnpj),
                )
                return cur.fetchone() is not None
            except Exception as exc:
                if erro_tabela_empresa_painel_arquivo_ausente(exc):
                    return False
                raise
    finally:
        conn.close()


def listar_cnpjs_arquivados_sync(dsn: str, tenant_id: UUID) -> frozenset[str]:
    import psycopg2

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    SELECT empresa_cnpj FROM empresa_painel_arquivo
                    WHERE tenant_id = %s
                    """,
                    (str(tenant_id),),
                )
                return frozenset(str(r[0]) for r in cur.fetchall())
            except Exception as exc:
                if erro_tabela_empresa_painel_arquivo_ausente(exc):
                    return frozenset()
                raise
    finally:
        conn.close()
