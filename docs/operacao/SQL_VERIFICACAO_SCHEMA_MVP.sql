-- Verificação somente leitura — MVP QDI (schema pós-migrações 0011/0012 + RLS).
-- Executar no SQL Editor do Supabase (ou psql) após aplicar migrações.
-- Esperado: cada subconsulta deve retornar exatamente uma linha com status = ok.

SELECT 'aceite_lgpd_0012' AS check_id,
       CASE
           WHEN EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_schema = 'public'
                 AND table_name = 'diagnosticos'
                 AND column_name = 'aceite_termos_privacidade_em'
           ) THEN 'ok'
           ELSE 'falta_coluna_aceite_termos_privacidade_em'
       END AS status;

SELECT 'locale_relatorio_0016' AS check_id,
       CASE
           WHEN EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_schema = 'public'
                 AND table_name = 'diagnosticos'
                 AND column_name = 'locale_relatorio'
           ) THEN 'ok'
           ELSE 'falta_coluna_locale_relatorio'
       END AS status;

SELECT 'm12_jsonb_0011' AS check_id,
       CASE
           WHEN EXISTS (
               SELECT 1
               FROM information_schema.columns
               WHERE table_schema = 'public'
                 AND table_name = 'diagnosticos'
                 AND column_name = 'checklist_m12_estado'
           ) THEN 'ok'
           ELSE 'falta_coluna_checklist_m12_estado'
       END AS status;

SELECT 'rls_diagnosticos' AS check_id,
       CASE
           WHEN EXISTS (
               SELECT 1
               FROM pg_class c
               JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = 'public'
                 AND c.relname = 'diagnosticos'
                 AND c.relrowsecurity = true
           ) THEN 'ok'
           ELSE 'rls_nao_habilitada'
       END AS status;

SELECT 'politicas_rls_count' AS check_id,
       CASE
           WHEN (
               SELECT count(*)::int
               FROM pg_policies
               WHERE schemaname = 'public'
                 AND tablename = 'diagnosticos'
           ) >= 4 THEN 'ok'
           ELSE 'politicas_insuficientes'
       END AS status;

SELECT 'fn_qdi_jwt_tenant_id' AS check_id,
       CASE
           WHEN EXISTS (
               SELECT 1
               FROM pg_proc p
               JOIN pg_namespace n ON n.oid = p.pronamespace
               WHERE n.nspname = 'public'
                 AND p.proname = 'qdi_jwt_tenant_id'
           ) THEN 'ok'
           ELSE 'falta_funcao_qdi_jwt_tenant_id'
       END AS status;

-- ---------------------------------------------------------------------------
-- Opcional — CNAE 2.3 (migrações 0013 + 0014). Executar após gate núcleo OK.
-- Equivale a `make verify-schema-mvp-strict` / script com --strict-cnae.
-- ---------------------------------------------------------------------------

SELECT 'ext_pg_trgm' AS check_id,
       CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')
            THEN 'ok' ELSE 'falta_extensao_pg_trgm' END AS status;

SELECT 'ext_pgcrypto' AS check_id,
       CASE WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgcrypto')
            THEN 'ok' ELSE 'falta_extensao_pgcrypto' END AS status;

SELECT 'qdi_cnae_subclasse_count' AS check_id,
       CASE
           WHEN NOT EXISTS (
               SELECT 1 FROM information_schema.tables
               WHERE table_schema = 'qdi' AND table_name = 'cnae_subclasse'
           ) THEN 'falta_tabela_qdi_cnae_subclasse'
           WHEN (SELECT count(*)::int FROM qdi.cnae_subclasse WHERE deleted_at IS NULL) = 1332
           THEN 'ok'
           ELSE 'contagem_subclasse_diferente_de_1332'
       END AS status;
