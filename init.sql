-- Orquestrador de bootstrap (PostgreSQL Docker) — DDL versionado em src/infrastructure/db/migrations/.
\set ON_ERROR_STOP on
\echo 'QualiDiagIQ: aplicando migrações...'
\i /docker-entrypoint-initdb.d/migrations/0001_extensions.sql
\i /docker-entrypoint-initdb.d/migrations/0002_schema_core.sql
\i /docker-entrypoint-initdb.d/migrations/0003_rls_policies.sql
\i /docker-entrypoint-initdb.d/migrations/0004_seed_dev_admin.sql
\i /docker-entrypoint-initdb.d/migrations/0005_worm_evidencia_audit.sql
\i /docker-entrypoint-initdb.d/migrations/0006_worm_column_granular.sql
\i /docker-entrypoint-initdb.d/migrations/0007_idempotency_responses.sql
\echo 'QualiDiagIQ: migrações concluídas.'
