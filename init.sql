-- Script de inicialização do banco de dados (PostgreSQL)
-- Cria as tabelas necessárias para o MVP do QualiDiagIQ

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de Administradores (Para o Dashboard B2B)
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    nome VARCHAR(255),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Diagnósticos
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

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_diagnosticos_tenant_id ON diagnosticos(tenant_id);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_status ON diagnosticos(status);

-- Inserir um usuário Admin Padrão (Senha temporária: admin123)
-- Nota: O hash bcrypt para 'admin123' é pré-calculado aqui para facilitar o ambiente DEV.
-- Em produção, os admins serão criados via API.
INSERT INTO admins (email, hashed_password, nome) 
VALUES ('allan@tributolab.com.br', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Admin Tributiq')
ON CONFLICT (email) DO NOTHING;
