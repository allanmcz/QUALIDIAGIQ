-- Extensões opcionais (pgvector, etc.) entram em migrações futuras.
-- Não usamos uuid-ossp aqui: em algumas imagens supabase/postgres o CREATE EXTENSION falha no init (owner supabase_admin).
-- IDs UUID com DEFAULT gen_random_uuid() (PostgreSQL 13+).

SELECT 1;
