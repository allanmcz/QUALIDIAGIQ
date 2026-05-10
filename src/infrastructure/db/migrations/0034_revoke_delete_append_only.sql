-- REVOKE DELETE em tabelas append-only (evidências forenses). Complementa políticas RLS.
-- ABNT NBR 17301:2026 — imutabilidade operacional onde aplicável.

REVOKE DELETE ON diagnostico_mutacao_audit FROM PUBLIC;
REVOKE DELETE ON diagnostico_mutacao_audit FROM authenticated;
REVOKE DELETE ON lgpd_anonimizacao_log FROM PUBLIC;
REVOKE DELETE ON lgpd_anonimizacao_log FROM authenticated;

COMMENT ON TABLE diagnostico_mutacao_audit IS
    'QDI — Log append-only de mutações em diagnosticos. DELETE revogado a authenticated/PUBLIC.';

COMMENT ON TABLE lgpd_anonimizacao_log IS
    'QDI — Log WORM anonimização LGPD. DELETE revogado a authenticated/PUBLIC.';
