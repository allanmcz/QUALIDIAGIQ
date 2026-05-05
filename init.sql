-- Orquestrador de bootstrap (PostgreSQL Docker) — DDL versionado em src/infrastructure/db/migrations/.
\set ON_ERROR_STOP on
\echo 'QualiDiagIQ: aplicando migrações...'
\i /docker-entrypoint-initdb.d/migrations/0001_extensions.sql
\i /docker-entrypoint-initdb.d/migrations/0002_schema_core.sql
\i /docker-entrypoint-initdb.d/migrations/0003_rls_policies.sql
\i /docker-entrypoint-initdb.d/migrations/0004_seed_dev_admin.sql
\i /docker-entrypoint-initdb.d/migrations/0005a_ci_playwright_admin.sql
\i /docker-entrypoint-initdb.d/migrations/0005b_worm_evidencia_audit.sql
\i /docker-entrypoint-initdb.d/migrations/0006_worm_column_granular.sql
\i /docker-entrypoint-initdb.d/migrations/0007_idempotency_responses.sql
\i /docker-entrypoint-initdb.d/migrations/0008_idempotency_comentarios_operacao.sql
\i /docker-entrypoint-initdb.d/migrations/0009_respondente_telefone_m10.sql
\i /docker-entrypoint-initdb.d/migrations/0010_rls_comentarios_documentacao_m10.sql
\i /docker-entrypoint-initdb.d/migrations/0011_checklist_m12_autoconf.sql
\i /docker-entrypoint-initdb.d/migrations/0012_aceite_lgpd_e_worm.sql
\i /docker-entrypoint-initdb.d/migrations/0013_cnae_referencia.sql
\i /docker-entrypoint-initdb.d/migrations/0014_cnae_seed_dados.sql
\i /docker-entrypoint-initdb.d/migrations/0015_normativa_score_macro_dimensao.sql
\i /docker-entrypoint-initdb.d/migrations/0016_locale_relatorio_pdf.sql
\i /docker-entrypoint-initdb.d/migrations/0017_empresa_faixa_faturamento_opcional.sql
\i /docker-entrypoint-initdb.d/migrations/0018_dev_admin_senha_admin123.sql
\i /docker-entrypoint-initdb.d/migrations/0019_rls_completo.sql
\i /docker-entrypoint-initdb.d/migrations/0020_pgvector_rag_light.sql
\i /docker-entrypoint-initdb.d/migrations/0021_admins_perfil_conta_dev.sql
\i /docker-entrypoint-initdb.d/migrations/0022_quadro_implantacao_anotacoes.sql
\i /docker-entrypoint-initdb.d/migrations/0023_diagnostico_rascunhos_self_service.sql
\i /docker-entrypoint-initdb.d/migrations/0024_diagnostico_leitura_publica_self_service.sql
\i /docker-entrypoint-initdb.d/migrations/0025_worm_permite_reatribuir_tenant_vinculo_lead.sql
\i /docker-entrypoint-initdb.d/migrations/0026_diagnostico_mutacao_audit.sql
\i /docker-entrypoint-initdb.d/migrations/0027_diagnostico_plano_materializado.sql
\echo 'QualiDiagIQ: migrações concluídas.'
