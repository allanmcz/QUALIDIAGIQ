-- QDI-H-003 — Hardening qdi_rag: sem escrita via roles de aplicação (defesa em profundidade).
-- Base: ingestão de normativos via scripts/service_role (Postgres); ``authenticated`` só SELECT (0020).
-- LGPD art. 46 / ABNT NBR 17301:2026 — integridade do repositório normativo.

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON qdi_rag.documento_normativo FROM authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON qdi_rag.documento_normativo FROM PUBLIC;

COMMENT ON TABLE qdi_rag.documento_normativo IS
    'Chunks normativos RAG-light — leitura authenticated; escrita apenas via roles privilegiadas (ingestão).';
