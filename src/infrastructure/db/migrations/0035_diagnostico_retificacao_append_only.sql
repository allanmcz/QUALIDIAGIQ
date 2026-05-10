-- Retificações append-only (ADR-012 §5) — cadeia NF-e/CC-e; não altera linha WORM do diagnóstico original.

CREATE TABLE IF NOT EXISTS diagnostico_retificacao (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    diagnostico_original_id UUID NOT NULL REFERENCES diagnosticos (id) ON DELETE CASCADE,
    hash_diagnostico_original_sha256 CHAR(64) NOT NULL,
    motivo_retificacao TEXT NOT NULL,
    payload_retificacao JSONB NOT NULL DEFAULT '{}'::jsonb,
    hash_retificacao_sha256 CHAR(64) NOT NULL,
    actor_user_id UUID NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_retificacao_hash_lower CHECK (
        hash_diagnostico_original_sha256 = lower(hash_diagnostico_original_sha256)
        AND hash_retificacao_sha256 = lower(hash_retificacao_sha256)
        AND length(hash_diagnostico_original_sha256) = 64
        AND length(hash_retificacao_sha256) = 64
    )
);

CREATE INDEX IF NOT EXISTS idx_diag_retif_tenant_diag
    ON diagnostico_retificacao (tenant_id, diagnostico_original_id, criado_em DESC);

COMMENT ON TABLE diagnostico_retificacao IS
    'QDI — retificações LGPD/compliance em cadeia (append-only); diagnóstico original imutável (WORM).';

ALTER TABLE diagnostico_retificacao ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diag_retif_tenant_insert ON diagnostico_retificacao;
CREATE POLICY diag_retif_tenant_insert ON diagnostico_retificacao
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS diag_retif_tenant_select ON diagnostico_retificacao;
CREATE POLICY diag_retif_tenant_select ON diagnostico_retificacao
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON diagnostico_retificacao TO authenticated;
