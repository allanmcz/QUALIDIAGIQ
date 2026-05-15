#!/usr/bin/env python3
"""
Verifica no Postgres alvo se o schema mínimo do MVP está presente (migrações até 0012 + RLS).

Modo estrito (``QDI_VERIFY_SCHEMA_STRICT_CNAE=1``): CNAE 0013/0014, tabela normativa de score macro (0015)
e tabela de overlay de pesos por pergunta (0042).

Uso (uma das opções):
  DATABASE_URL=postgresql://user:pass@host:5432/db python scripts/verify_mvp_schema.py
  QDI_POSTGRES_TEST_URL=postgresql://... python scripts/verify_mvp_schema.py
  python scripts/verify_mvp_schema.py postgresql://user:pass@host:5432/db
  QDI_VERIFY_SCHEMA_STRICT_CNAE=1 make verify-schema-mvp
  python scripts/verify_mvp_schema.py --strict-cnae postgresql://...
  QDI_VERIFY_SCHEMA_RAG=1 python scripts/verify_mvp_schema.py
  python scripts/verify_mvp_schema.py --rag postgresql://...

Aceita URL com prefixo ``postgresql+asyncpg://`` (normaliza para asyncpg).

Saída: mensagens em PT-BR; código de saída 0 = OK, 1 = falha.

Camada: ferramenta de operação (fora da Clean Architecture — apenas diagnóstico de infra).
"""

from __future__ import annotations

import asyncio
import os
import sys

import asyncpg


def _dsn_normalizado(raw: str) -> str:
    return raw.strip().replace("postgresql+asyncpg://", "postgresql://", 1)


def _parse_argv(argv: list[str]) -> tuple[str | None, bool, bool]:
    strict_cnae = os.environ.get("QDI_VERIFY_SCHEMA_STRICT_CNAE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    rag_light = os.environ.get("QDI_VERIFY_SCHEMA_RAG", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )
    dsn: str | None = None
    for a in argv:
        if a == "--strict-cnae":
            strict_cnae = True
        elif a == "--rag":
            rag_light = True
        elif not a.startswith("-"):
            dsn = a
    return dsn, strict_cnae, rag_light


async def _verificar_nucleo(conn: asyncpg.Connection) -> list[str]:
    erros: list[str] = []

    aceite = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'aceite_termos_privacidade_em'
    """)
    if aceite != 1:
        erros.append(
            "Coluna public.diagnosticos.aceite_termos_privacidade_em ausente "
            "(aplique migração 0012 ou equivalente)."
        )

    loc_pdf = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'locale_relatorio'
    """)
    if loc_pdf != 1:
        erros.append("Coluna public.diagnosticos.locale_relatorio ausente (aplique migração 0016).")

    ff_col = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'empresa_faixa_faturamento'
    """)
    if ff_col != 1:
        erros.append(
            "Coluna public.diagnosticos.empresa_faixa_faturamento ausente (aplique migração 0017)."
        )

    m12 = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'checklist_m12_estado'
    """)
    if m12 != 1:
        erros.append("Coluna public.diagnosticos.checklist_m12_estado ausente (migração 0011).")

    vp = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'versao_plano'
    """)
    if vp != 1:
        erros.append("Coluna public.diagnosticos.versao_plano ausente (migração 0027).")

    ip_origem = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'respondente_ip_origem'
    """)
    if ip_origem != 1:
        erros.append("Coluna public.diagnosticos.respondente_ip_origem ausente (migração 0036).")

    plano_tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'diagnostico_plano_acao'
    """)
    if plano_tbl != 1:
        erros.append("Tabela public.diagnostico_plano_acao ausente (migração 0027).")

    rls = await conn.fetchval("""
        SELECT c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'diagnosticos'
    """)
    if rls is not True:
        erros.append(
            "RLS não habilitada em public.diagnosticos (ver migração 0003_rls_policies.sql)."
        )

    n_pol = await conn.fetchval("""
        SELECT count(*)::int
        FROM pg_policies
        WHERE schemaname = 'public' AND tablename = 'diagnosticos'
    """)
    if (n_pol or 0) < 4:
        erros.append(f"Esperadas políticas RLS em diagnosticos (>=4); encontradas: {n_pol or 0}.")

    fn = await conn.fetchval("""
        SELECT 1
        FROM pg_proc p
        JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'public' AND p.proname = 'qdi_jwt_tenant_id'
    """)
    if fn != 1:
        erros.append("Função public.qdi_jwt_tenant_id ausente (necessária para políticas RLS).")

    idem_tid = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'idempotency_responses'
          AND column_name = 'tenant_id'
    """)
    if idem_tid != 1:
        erros.append(
            "Coluna public.idempotency_responses.tenant_id ausente (aplique migração 0019)."
        )

    adm_rls = await conn.fetchval("""
        SELECT c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'admins'
    """)
    if adm_rls is not True:
        erros.append("RLS não habilitada em public.admins (migração 0019_rls_completo).")

    dma = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'diagnostico_mutacao_audit'
    """)
    if dma != 1:
        erros.append("Tabela public.diagnostico_mutacao_audit ausente (aplique migração 0026).")
    else:
        dma_rls = await conn.fetchval("""
            SELECT c.relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = 'diagnostico_mutacao_audit'
        """)
        if dma_rls is not True:
            erros.append("RLS não habilitada em public.diagnostico_mutacao_audit (migração 0026).")

    erros.extend(await _verificar_explicacao_score_llm_schema(conn))
    return erros


async def _verificar_explicacao_score_llm_schema(conn: asyncpg.Connection) -> list[str]:
    """Migrações 0043–0045 — narrativa LLM do score + histórico + ledger de quota."""
    erros: list[str] = []

    expl_col = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'diagnosticos'
          AND column_name = 'explicacao_score_llm'
    """)
    if expl_col != 1:
        erros.append(
            "Coluna public.diagnosticos.explicacao_score_llm ausente (aplique migração 0043)."
        )

    hist_tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'diagnostico_explicacao_score_llm_historico'
    """)
    if hist_tbl != 1:
        erros.append(
            "Tabela public.diagnostico_explicacao_score_llm_historico ausente (migração 0044)."
        )
    else:
        hist_rls = await conn.fetchval("""
            SELECT c.relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relname = 'diagnostico_explicacao_score_llm_historico'
        """)
        if hist_rls is not True:
            erros.append(
                "RLS não habilitada em public.diagnostico_explicacao_score_llm_historico (0044)."
            )

    ledger_tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'llm_tenant_usage_ledger'
    """)
    if ledger_tbl != 1:
        erros.append("Tabela public.llm_tenant_usage_ledger ausente (migração 0045).")

    perfil_ci = await conn.fetchval("""
        SELECT perfil_conta
        FROM admins
        WHERE lower(trim(email)) = lower(trim('ci-dashboard@qualidiagiq.test'))
        LIMIT 1
    """)
    if perfil_ci is None:
        erros.append("Admin ci-dashboard@qualidiagiq.test ausente (0005a / seed CI).")
    elif str(perfil_ci).strip().lower() != "avancado":
        erros.append(
            "Admin CI deve ter perfil_conta=avancado para smoke LLM (migração 0046)."
        )

    return erros


async def _verificar_normativa_score_macro_strict(conn: asyncpg.Connection) -> list[str]:
    """Migração 0015 — pesos macro por dimensão (épico E1)."""
    erros: list[str] = []

    tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'qdi' AND table_name = 'normativa_score_macro_dimensao'
    """)
    if tbl != 1:
        erros.append("Tabela qdi.normativa_score_macro_dimensao ausente (aplique migração 0015).")
        return erros

    cnt = await conn.fetchval("""
        SELECT count(DISTINCT dimensao)::int
        FROM qdi.normativa_score_macro_dimensao
    """)
    esperado_dimensoes = 7
    if (cnt or 0) < esperado_dimensoes:
        erros.append(
            f"Esperadas ao menos {esperado_dimensoes} dimensões distintas em "
            f"qdi.normativa_score_macro_dimensao; encontradas: {cnt or 0}."
        )

    return erros


async def _verificar_normativa_pergunta_peso_strict(conn: asyncpg.Connection) -> list[str]:
    """Migração 0042 — overlay de pesos por pergunta (catálogo JSON)."""
    erros: list[str] = []

    tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'qdi' AND table_name = 'normativa_pergunta_peso'
    """)
    if tbl != 1:
        erros.append("Tabela qdi.normativa_pergunta_peso ausente (aplique migração 0042).")
        return erros

    rls = await conn.fetchval("""
        SELECT c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'qdi' AND c.relname = 'normativa_pergunta_peso'
    """)
    if rls is not True:
        erros.append("RLS não habilitada em qdi.normativa_pergunta_peso (migração 0042).")

    return erros


async def _verificar_strict_cnae(conn: asyncpg.Connection) -> list[str]:
    erros: list[str] = []

    for ext in ("pg_trgm", "pgcrypto"):
        ex = await conn.fetchval(
            "SELECT 1 FROM pg_extension WHERE extname = $1",
            ext,
        )
        if ex != 1:
            erros.append(
                f"Extensão PostgreSQL '{ext}' ausente (necessária para migração 0013 CNAE)."
            )

    tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'qdi' AND table_name = 'cnae_subclasse'
    """)
    if tbl != 1:
        erros.append("Tabela qdi.cnae_subclasse ausente (aplique migrações 0013 e 0014).")
        return erros

    cnt = await conn.fetchval(
        "SELECT count(*)::int FROM qdi.cnae_subclasse WHERE deleted_at IS NULL"
    )
    esperado = 1332
    if (cnt or 0) != esperado:
        erros.append(
            f"Contagem qdi.cnae_subclasse (sem deleted_at) esperada {esperado}; encontrada {cnt!r}."
        )

    return erros


async def _verificar_rag_light(conn: asyncpg.Connection) -> list[str]:
    """Migração 0020 — extensão vector + tabela ``qdi_rag.documento_normativo``."""
    erros: list[str] = []

    ext = await conn.fetchval(
        "SELECT 1 FROM pg_extension WHERE extname = $1",
        "vector",
    )
    if ext != 1:
        erros.append("Extensão PostgreSQL 'vector' ausente (migração 0020 / imagem pgvector).")

    tbl = await conn.fetchval("""
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'qdi_rag' AND table_name = 'documento_normativo'
    """)
    if tbl != 1:
        erros.append("Tabela qdi_rag.documento_normativo ausente (aplique migração 0020).")
        return erros

    emb = await conn.fetchval("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'qdi_rag'
          AND table_name = 'documento_normativo'
          AND column_name = 'embedding'
    """)
    if emb != 1:
        erros.append("Coluna qdi_rag.documento_normativo.embedding ausente.")

    return erros


async def _verificar(conn_dsn: str, *, strict_cnae: bool, rag_light: bool) -> list[str]:
    conn = await asyncpg.connect(conn_dsn, timeout=10)
    try:
        erros = await _verificar_nucleo(conn)
        if strict_cnae:
            erros.extend(await _verificar_strict_cnae(conn))
            erros.extend(await _verificar_normativa_score_macro_strict(conn))
            erros.extend(await _verificar_normativa_pergunta_peso_strict(conn))
        if rag_light:
            erros.extend(await _verificar_rag_light(conn))
        return erros
    finally:
        await conn.close()


def main() -> int:
    dsn_arg, strict_cnae, rag_light = _parse_argv(sys.argv[1:])
    raw_url = dsn_arg or os.environ.get("DATABASE_URL") or os.environ.get("QDI_POSTGRES_TEST_URL")
    if not raw_url:
        print(
            "Defina DATABASE_URL, QDI_POSTGRES_TEST_URL ou passe a DSN como argumento.",
            file=sys.stderr,
        )
        print(
            "Modo CNAE estrito: --strict-cnae ou QDI_VERIFY_SCHEMA_STRICT_CNAE=1",
            file=sys.stderr,
        )
        print(
            "Modo RAG-light: --rag ou QDI_VERIFY_SCHEMA_RAG=1",
            file=sys.stderr,
        )
        return 1

    dsn = _dsn_normalizado(raw_url)

    try:
        erros = asyncio.run(_verificar(dsn, strict_cnae=strict_cnae, rag_light=rag_light))
    except Exception as exc:
        print(f"Falha de conexão ou execução: {exc}", file=sys.stderr)
        return 1

    if erros:
        print("Verificação MVP schema: FALHA", file=sys.stderr)
        for e in erros:
            print(f"  - {e}", file=sys.stderr)
        return 1

    msg = (
        "Verificação MVP schema: OK (0012 + M12 + RLS + qdi_jwt_tenant_id + 0026 auditoria mutação "
        "+ explicacao_score_llm 0043–0046)."
    )
    if strict_cnae:
        msg += " Modo strict: CNAE (extensões + 1332 subclasses) + normativa score macro (0015)."
    if rag_light:
        msg += " Modo RAG: extensão vector + qdi_rag.documento_normativo (0020)."
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
