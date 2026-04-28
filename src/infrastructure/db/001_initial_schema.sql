-- Schema Inicial: QualiDiagIQ
-- Sprint 1: Tabela de Diagnósticos e Isolamento Multi-tenant (RLS)

-- 1. Tabela de Diagnosticos
CREATE TABLE IF NOT EXISTS diagnosticos (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL, -- Obrigatório para o RLS
    respondente_email TEXT NOT NULL,
    respondente_nome TEXT,
    respondente_cargo TEXT,
    empresa_cnpj VARCHAR(14) NOT NULL,
    empresa_razao_social TEXT NOT NULL,
    empresa_porte TEXT NOT NULL,
    empresa_regime TEXT NOT NULL,
    empresa_cnae TEXT NOT NULL,
    empresa_uf VARCHAR(2) NOT NULL,
    empresa_setor_macro TEXT NOT NULL,
    status TEXT NOT NULL,
    score_geral NUMERIC(5,2),
    relatorio_pdf_url TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizado_em TIMESTAMPTZ,
    
    CONSTRAINT chk_status CHECK (status IN ('em_andamento', 'finalizado', 'expirado', 'cancelado'))
);

-- 2. Índices de performance
CREATE INDEX IF NOT EXISTS idx_diagnosticos_tenant_id ON diagnosticos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_status ON diagnosticos(status);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_cnpj ON diagnosticos(empresa_cnpj);

-- 3. Habilitando Row Level Security (RLS)
ALTER TABLE diagnosticos ENABLE ROW LEVEL SECURITY;

-- 4. Criando as Policies (Segurança Isolada)
-- Apenas usuários/sistemas autenticados com o JWT do Tenant podem ver e modificar seus dados
CREATE POLICY "Isolamento Multi-tenant: SELECT" ON diagnosticos
    FOR SELECT
    USING (tenant_id = auth.uid());

CREATE POLICY "Isolamento Multi-tenant: INSERT" ON diagnosticos
    FOR INSERT
    WITH CHECK (tenant_id = auth.uid());

CREATE POLICY "Isolamento Multi-tenant: UPDATE" ON diagnosticos
    FOR UPDATE
    USING (tenant_id = auth.uid())
    WITH CHECK (tenant_id = auth.uid());
