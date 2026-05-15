-- Histórico append-only de narrativas LLM sobre o score (painel).
-- A coluna diagnosticos.explicacao_score_llm mantém a última geração; esta tabela preserva todas.

CREATE TABLE IF NOT EXISTS diagnostico_explicacao_score_llm_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos (id) ON DELETE CASCADE,
    snapshot JSONB NOT NULL,
    actor_user_id UUID NULL,
    trace_id VARCHAR(128) NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_explic_llm_hist_tenant_diag
    ON diagnostico_explicacao_score_llm_historico (tenant_id, diagnostico_id, criado_em DESC);

COMMENT ON TABLE diagnostico_explicacao_score_llm_historico IS
    'QDI — histórico append-only de POST /diagnosticos/{id}/explicacao-score-llm (ADR-022).';

CREATE OR REPLACE FUNCTION qdi_tr_block_explicacao_llm_hist_upd_del()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'diagnostico_explicacao_score_llm_historico é append-only (UPDATE/DELETE proibidos)';
END;
$$;

DROP TRIGGER IF EXISTS tr_explic_llm_hist_append_only ON diagnostico_explicacao_score_llm_historico;
CREATE TRIGGER tr_explic_llm_hist_append_only
    BEFORE UPDATE OR DELETE ON diagnostico_explicacao_score_llm_historico
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_block_explicacao_llm_hist_upd_del();

ALTER TABLE diagnostico_explicacao_score_llm_historico ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS expl_llm_hist_tenant_insert ON diagnostico_explicacao_score_llm_historico;
CREATE POLICY expl_llm_hist_tenant_insert ON diagnostico_explicacao_score_llm_historico
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS expl_llm_hist_tenant_select ON diagnostico_explicacao_score_llm_historico;
CREATE POLICY expl_llm_hist_tenant_select ON diagnostico_explicacao_score_llm_historico
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON diagnostico_explicacao_score_llm_historico TO authenticated;
