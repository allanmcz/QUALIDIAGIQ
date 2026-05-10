-- FORCE ROW LEVEL SECURITY — políticas aplicáveis também ao owner não superusuário (defesa em profundidade).
-- LGPD art. 46 + ABNT NBR 17301:2026 — segurança do tratamento.
--
-- Superusuários PostgreSQL continuam a contornar RLS; uso típico em Docker (postgres) mantém bypass.

ALTER TABLE diagnosticos FORCE ROW LEVEL SECURITY;
ALTER TABLE lgpd_titular_solicitacao FORCE ROW LEVEL SECURITY;
ALTER TABLE lgpd_anonimizacao_log FORCE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_mutacao_audit FORCE ROW LEVEL SECURITY;

COMMENT ON TABLE diagnosticos IS
    'QDI — Agregado Diagnostico. RLS + FORCE ativo em políticas tenant-scoped.';
