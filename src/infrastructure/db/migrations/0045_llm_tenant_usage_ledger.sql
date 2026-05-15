-- Ledger append-only de uso LLM por tenant (quotas ADR-022 Fase 4 — MVP).

CREATE TABLE IF NOT EXISTS llm_tenant_usage_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    task_type VARCHAR(48) NOT NULL,
    trace_id VARCHAR(128) NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_tenant_task_dia
    ON llm_tenant_usage_ledger (tenant_id, task_type, criado_em DESC);

COMMENT ON TABLE llm_tenant_usage_ledger IS
    'QDI — eventos de conclusão LLM por tenant (contagem diária para quota; append-only).';

ALTER TABLE llm_tenant_usage_ledger ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS llm_usage_tenant_insert ON llm_tenant_usage_ledger;
CREATE POLICY llm_usage_tenant_insert ON llm_tenant_usage_ledger
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS llm_usage_tenant_select ON llm_tenant_usage_ledger;
CREATE POLICY llm_usage_tenant_select ON llm_tenant_usage_ledger
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON llm_tenant_usage_ledger TO authenticated;
