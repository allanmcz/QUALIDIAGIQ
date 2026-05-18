-- Onda IA 1.1 — Fase H: checkpoint LangGraph do wizard (memória episódica).

CREATE TABLE IF NOT EXISTS qdi.wizard_langgraph_checkpoint (
    thread_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    checkpoint JSONB NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wizard_checkpoint_tenant
    ON qdi.wizard_langgraph_checkpoint (tenant_id, atualizado_em DESC);

ALTER TABLE qdi.wizard_langgraph_checkpoint ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS wizard_checkpoint_tenant ON qdi.wizard_langgraph_checkpoint;
CREATE POLICY wizard_checkpoint_tenant ON qdi.wizard_langgraph_checkpoint
    FOR ALL TO authenticated
    USING (tenant_id = (current_setting('app.tenant_id', true))::uuid)
    WITH CHECK (tenant_id = (current_setting('app.tenant_id', true))::uuid);

COMMENT ON TABLE qdi.wizard_langgraph_checkpoint IS
    'Checkpoint LangGraph do wizard QDI — thread_id estável por sessão de preenchimento.';
