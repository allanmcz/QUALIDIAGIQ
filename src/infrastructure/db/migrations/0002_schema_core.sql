-- Núcleo de tabelas públicas — alinhado ao bootstrap local e ao cliente Supabase (tabela "diagnosticos", "admins").
-- Multi-tenant: isolamento em application + RLS em diagnosticos (ver 0003_rls_policies.sql).

CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    nome VARCHAR(255),
    tenant_id UUID NOT NULL DEFAULT '33333333-3333-4333-8333-333333333333'::uuid,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Compat: bases criadas por init legado sem tenant_id na CREATE inicial
ALTER TABLE admins ADD COLUMN IF NOT EXISTS tenant_id UUID DEFAULT '33333333-3333-4333-8333-333333333333'::uuid;
UPDATE admins SET tenant_id = '33333333-3333-4333-8333-333333333333'::uuid WHERE tenant_id IS NULL;
ALTER TABLE admins ALTER COLUMN tenant_id SET NOT NULL;
ALTER TABLE admins ALTER COLUMN tenant_id SET DEFAULT '33333333-3333-4333-8333-333333333333'::uuid;

CREATE TABLE IF NOT EXISTS diagnosticos (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    respondente_email VARCHAR(255),
    respondente_nome VARCHAR(255),
    respondente_cargo VARCHAR(255),
    empresa_cnpj VARCHAR(14) NOT NULL,
    empresa_razao_social VARCHAR(255) NOT NULL,
    empresa_porte VARCHAR(50) NOT NULL,
    empresa_regime VARCHAR(50) NOT NULL,
    empresa_cnae VARCHAR(10),
    empresa_uf VARCHAR(2),
    empresa_setor_macro VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    plano VARCHAR(50) DEFAULT 'gratuito',
    score_geral DOUBLE PRECISION,
    relatorio_pdf_url TEXT,
    criado_em TIMESTAMP WITH TIME ZONE NOT NULL,
    finalizado_em TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_diagnosticos_tenant_id ON diagnosticos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_status ON diagnosticos(status);
