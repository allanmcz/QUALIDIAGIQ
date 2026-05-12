-- QDI-H-004 (complemento) — FORCE RLS em trilhas de consulta CNPJ (schema public, migração 0030).
-- Corrige lacuna onde 0038 referia nomes legados ``cnae_referencia`` / ``cnpj_consulta_cache`` inexistentes neste repo.

ALTER TABLE IF EXISTS cnpj_consultas FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS diagnostico_empresa_campo_historico FORCE ROW LEVEL SECURITY;