-- Arquivo operacional de empresa no painel (CNPJ por tenant) — não apaga evidência WORM.
-- Oculta da listagem principal; diagnósticos finalizados permanecem na BD.

CREATE TABLE IF NOT EXISTS empresa_painel_arquivo (
    tenant_id UUID NOT NULL,
    empresa_cnpj CHAR(14) NOT NULL,
    arquivado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    arquivado_por_user_id UUID,
    PRIMARY KEY (tenant_id, empresa_cnpj),
    CONSTRAINT chk_empresa_painel_arquivo_cnpj CHECK (empresa_cnpj ~ '^\d{14}$')
);

COMMENT ON TABLE empresa_painel_arquivo IS
    'Empresas (CNPJ) ocultas do painel principal — reversível sem tocar em diagnósticos finalizados (WORM).';

CREATE INDEX IF NOT EXISTS idx_empresa_painel_arquivo_tenant
    ON empresa_painel_arquivo (tenant_id);

ALTER TABLE empresa_painel_arquivo ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresa_painel_arquivo FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS empresa_painel_arquivo_tenant_all ON empresa_painel_arquivo;
CREATE POLICY empresa_painel_arquivo_tenant_all ON empresa_painel_arquivo
    FOR ALL
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON empresa_painel_arquivo TO authenticated;
