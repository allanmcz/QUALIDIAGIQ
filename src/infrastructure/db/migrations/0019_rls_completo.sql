-- Sprint 11 handoff — RLS em admins + idempotency_responses.tenant_id + políticas tenant-scoped.
-- Referência CNAE (qdi.cnae_*) e qdi.cnae_importacao_log já possuem RLS na migração 0013.

-- ─── admins ─────────────────────────────────────────────────────────────
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS admins_tenant_select ON admins;
CREATE POLICY admins_tenant_select ON admins
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS admins_tenant_modify ON admins;
CREATE POLICY admins_tenant_modify ON admins
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON admins TO authenticated;

-- ─── idempotency_responses (isolamento por tenant para clientes JWT) ────
ALTER TABLE idempotency_responses ADD COLUMN IF NOT EXISTS tenant_id UUID;

UPDATE idempotency_responses
SET tenant_id = '00000000-0000-0000-0000-000000000000'::uuid
WHERE tenant_id IS NULL;

ALTER TABLE idempotency_responses ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE idempotency_responses
    ALTER COLUMN tenant_id SET DEFAULT '00000000-0000-0000-0000-000000000000'::uuid;

ALTER TABLE idempotency_responses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS idempotency_tenant ON idempotency_responses;
CREATE POLICY idempotency_tenant ON idempotency_responses
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON idempotency_responses TO authenticated;
