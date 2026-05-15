-- Narrativa LLM sobre o score (ADR-022) — mutável após finalizado; fora do hash WORM.
-- Padrão: checklist_m12_estado / quadro_implantacao_anotacoes (não listados em qdi_tr_block_mutacao_pos_finalizacao).

ALTER TABLE diagnosticos
    ADD COLUMN IF NOT EXISTS explicacao_score_llm JSONB NULL;

COMMENT ON COLUMN diagnosticos.explicacao_score_llm IS
    'Última narrativa POST /diagnosticos/{id}/explicacao-score-llm: texto, provider, model, '
    'policy_version, guardrails, tokens, latency_ms, gerado_em (UTC), trace_id. '
    'Não altera score_completo nem hash_sha256.';
