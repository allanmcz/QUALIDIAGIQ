-- QDI-H-004 — FORCE ROW LEVEL SECURITY em tabelas residuais (defesa em profundidade).
-- Alinhado a políticas multi-tenant e LGPD art. 46.

ALTER TABLE IF EXISTS idempotency_responses FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cnae_referencia FORCE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS cnpj_consulta_cache FORCE ROW LEVEL SECURITY;
