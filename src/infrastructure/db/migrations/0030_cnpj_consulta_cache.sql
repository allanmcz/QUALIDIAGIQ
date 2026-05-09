-- =====================================================================
-- MIGRATION 0030 — Consulta CNPJ (cache auditável + histórico de merge empresa)
-- Produto: QualiDiagIQ — BrasilAPI com fallback Minha Receita (falha/timeout).
-- Multi-tenant: tenant_id UUID sem FK (padrão projeto); RLS via qdi_jwt_tenant_id().
-- =====================================================================

CREATE TABLE IF NOT EXISTS cnpj_consultas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    cnpj CHAR(14) NOT NULL,
    diagnostico_id UUID NULL REFERENCES diagnosticos (id) ON DELETE SET NULL,
    payload_bruto JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_canonico JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload_hash CHAR(64) NOT NULL,
    fonte VARCHAR(32) NOT NULL,
    consultado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expira_cadastral_at TIMESTAMPTZ NOT NULL,
    expira_qualificacao_at TIMESTAMPTZ NOT NULL,
    expira_situacao_at TIMESTAMPTZ NOT NULL,
    latencia_ms INTEGER NULL,
    http_status SMALLINT NULL,
    trace_id VARCHAR(128) NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_cnpj_consultas_fonte CHECK (fonte IN ('brasil_api', 'minha_receita')),
    CONSTRAINT uq_cnpj_consultas_tenant_idempotency UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_cnpj_consultas_tenant_cnpj_em
    ON cnpj_consultas (tenant_id, cnpj, consultado_em DESC);

COMMENT ON TABLE cnpj_consultas IS
    'QDI — snapshots de consulta CNPJ por tenant; TTL triplo (cadastral/qualificação/situação) em env.';

CREATE TABLE IF NOT EXISTS diagnostico_empresa_campo_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos (id) ON DELETE CASCADE,
    cnpj_consulta_id UUID NULL REFERENCES cnpj_consultas (id) ON DELETE SET NULL,
    campo VARCHAR(64) NOT NULL,
    valor_anterior TEXT NULL,
    valor_novo TEXT NOT NULL,
    alterado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_diagnostico_empresa_hist_campo CHECK (
        campo IN (
            'empresa_cnpj',
            'empresa_razao_social',
            'empresa_cnae',
            'empresa_uf',
            'empresa_porte',
            'empresa_regime',
            'empresa_setor_macro'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_diagnostico_empresa_hist_tenant_diag
    ON diagnostico_empresa_campo_historico (tenant_id, diagnostico_id, alterado_em DESC);

COMMENT ON TABLE diagnostico_empresa_campo_historico IS
    'QDI — append-only: valores anteriores ao preenchimento/sobrescrita via consulta CNPJ (LC 214/2025 — previsibilidade; LGPD minimização).';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ RLS (clientes Supabase authenticated)                             │
-- └────────────────────────────────────────────────────────────────────┘

ALTER TABLE cnpj_consultas ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS cnpj_consultas_tenant_insert ON cnpj_consultas;
CREATE POLICY cnpj_consultas_tenant_insert ON cnpj_consultas
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS cnpj_consultas_tenant_select ON cnpj_consultas;
CREATE POLICY cnpj_consultas_tenant_select ON cnpj_consultas
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON cnpj_consultas TO authenticated;

ALTER TABLE diagnostico_empresa_campo_historico ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagnostico_empresa_hist_tenant_insert ON diagnostico_empresa_campo_historico;
CREATE POLICY diagnostico_empresa_hist_tenant_insert ON diagnostico_empresa_campo_historico
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS diagnostico_empresa_hist_tenant_select ON diagnostico_empresa_campo_historico;
CREATE POLICY diagnostico_empresa_hist_tenant_select ON diagnostico_empresa_campo_historico
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON diagnostico_empresa_campo_historico TO authenticated;
