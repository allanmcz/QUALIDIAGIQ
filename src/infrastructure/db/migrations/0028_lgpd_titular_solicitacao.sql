-- Base técnica LGPD (art. 18): solicitações do titular em trilha append-only.
-- Não implementa endpoint público; serve de fundação para fluxo posterior após decisão jurídica (ADR-012).

CREATE TABLE IF NOT EXISTS lgpd_titular_solicitacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    diagnostico_id UUID NULL,
    tipo VARCHAR(32) NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'recebida',
    canal VARCHAR(24) NOT NULL DEFAULT 'plataforma',
    solicitante_email VARCHAR(254) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    observacao_interna TEXT NULL,
    actor_user_id UUID NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_lgpd_tipo CHECK (
        tipo IN ('acesso', 'correcao', 'anonimizacao', 'eliminacao', 'portabilidade', 'oposicao')
    ),
    CONSTRAINT chk_lgpd_status CHECK (
        status IN ('recebida', 'em_analise', 'deferida', 'indeferida', 'concluida')
    ),
    CONSTRAINT chk_lgpd_canal CHECK (
        canal IN ('plataforma', 'self_service', 'dpo_email')
    )
);

CREATE INDEX IF NOT EXISTS idx_lgpd_solicitacao_tenant_criado
    ON lgpd_titular_solicitacao (tenant_id, criado_em DESC);
CREATE INDEX IF NOT EXISTS idx_lgpd_solicitacao_tenant_status
    ON lgpd_titular_solicitacao (tenant_id, status);

COMMENT ON TABLE lgpd_titular_solicitacao IS
    'QDI — solicitações do titular LGPD (art. 18) por tenant; base para fluxo auditável de privacidade.';

CREATE OR REPLACE FUNCTION qdi_tr_lgpd_touch_atualizado_em()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_lgpd_touch_atualizado_em ON lgpd_titular_solicitacao;
CREATE TRIGGER tr_lgpd_touch_atualizado_em
    BEFORE UPDATE ON lgpd_titular_solicitacao
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_lgpd_touch_atualizado_em();

ALTER TABLE lgpd_titular_solicitacao ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS lgpd_solicitacao_tenant_insert ON lgpd_titular_solicitacao;
CREATE POLICY lgpd_solicitacao_tenant_insert ON lgpd_titular_solicitacao
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS lgpd_solicitacao_tenant_select ON lgpd_titular_solicitacao;
CREATE POLICY lgpd_solicitacao_tenant_select ON lgpd_titular_solicitacao
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS lgpd_solicitacao_tenant_update ON lgpd_titular_solicitacao;
CREATE POLICY lgpd_solicitacao_tenant_update ON lgpd_titular_solicitacao
    FOR UPDATE TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE ON lgpd_titular_solicitacao TO authenticated;
