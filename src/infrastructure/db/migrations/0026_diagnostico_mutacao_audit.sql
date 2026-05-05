-- Log append-only de mutações permitidas após finalização (M12 Likert, quadro de implantação, URL do PDF).
-- Complementa o WORM granular em ``diagnosticos`` (0012/0016/0025): rastreabilidade LC 214/2025; evidências ABNT NBR 17301:2026.

CREATE TABLE IF NOT EXISTS diagnostico_mutacao_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    diagnostico_id UUID NOT NULL,
    tipo VARCHAR(48) NOT NULL,
    payload JSONB NOT NULL,
    actor_user_id UUID NULL,
    versao_otimista_antes INTEGER NOT NULL,
    versao_otimista_apos INTEGER NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_dma_tipo CHECK (
        tipo IN ('m12_likert', 'quadro_implantacao', 'relatorio_pdf')
    )
);

CREATE INDEX IF NOT EXISTS idx_dma_tenant_diag
    ON diagnostico_mutacao_audit (tenant_id, diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_dma_criado ON diagnostico_mutacao_audit (criado_em DESC);

COMMENT ON TABLE diagnostico_mutacao_audit IS
    'QDI — eventos append-only de PATCH pós-finalização (M12, quadro, PDF) com actor e versão otimista.';

CREATE OR REPLACE FUNCTION qdi_tr_block_mutacao_audit_upd_del()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'diagnostico_mutacao_audit é append-only (UPDATE/DELETE proibidos)';
END;
$$;

DROP TRIGGER IF EXISTS tr_dma_append_only ON diagnostico_mutacao_audit;
CREATE TRIGGER tr_dma_append_only
    BEFORE UPDATE OR DELETE ON diagnostico_mutacao_audit
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_block_mutacao_audit_upd_del();

ALTER TABLE diagnostico_mutacao_audit ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS dma_tenant_insert ON diagnostico_mutacao_audit;
CREATE POLICY dma_tenant_insert ON diagnostico_mutacao_audit
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS dma_tenant_select ON diagnostico_mutacao_audit;
CREATE POLICY dma_tenant_select ON diagnostico_mutacao_audit
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON diagnostico_mutacao_audit TO authenticated;
