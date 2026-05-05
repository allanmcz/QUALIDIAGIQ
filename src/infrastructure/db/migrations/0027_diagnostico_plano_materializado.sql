-- Materialização do plano de ação / matriz M06 / cronograma (snapshot auditável por diagnóstico).
-- Decisões: D1 (finalização + backfill separado), D2 (mesmo snapshot), D3 (versao_plano), D4/D5 (filhas + subtarefas).
-- Base: LC 214/2025 (rastreabilidade); ABNT NBR 17301:2026 cap. 7 (evidências operacionais).

-- Versão lógica do plano materializado (incremento explícito futuro — motor / regeneração).
ALTER TABLE diagnosticos
    ADD COLUMN IF NOT EXISTS versao_plano INTEGER NOT NULL DEFAULT 1
    CONSTRAINT diagnosticos_versao_plano_chk CHECK (versao_plano >= 1);

CREATE TABLE IF NOT EXISTS diagnostico_plano_acao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    versao_plano INTEGER NOT NULL DEFAULT 1,
    ordem_exibicao INTEGER NOT NULL,
    frente_indice INTEGER NOT NULL,
    acao_indice INTEGER NOT NULL,
    frente_nome TEXT NOT NULL,
    texto_acao TEXT NOT NULL,
    responsavel_sugerido VARCHAR(255) NOT NULL DEFAULT '',
    prazo_sugerido_texto VARCHAR(255) NOT NULL DEFAULT '',
    criticidade VARCHAR(64) NOT NULL DEFAULT '',
    base_legal TEXT,
    origem_motor VARCHAR(32) NOT NULL DEFAULT 'OUTROS',
    prioridade_motor INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT diagnostico_plano_acao_versao_chk CHECK (versao_plano >= 1),
    CONSTRAINT diagnostico_plano_acao_ordem_chk CHECK (ordem_exibicao >= 0),
    CONSTRAINT diagnostico_plano_acao_fi_chk CHECK (frente_indice >= 0),
    CONSTRAINT diagnostico_plano_acao_ai_chk CHECK (acao_indice >= 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_diagnostico_plano_acao_diag_versao_ordem
    ON diagnostico_plano_acao(diagnostico_id, versao_plano, ordem_exibicao);

CREATE INDEX IF NOT EXISTS idx_diagnostico_plano_acao_tenant_diag
    ON diagnostico_plano_acao(tenant_id, diagnostico_id);

CREATE TABLE IF NOT EXISTS diagnostico_plano_subtarefa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plano_acao_id UUID NOT NULL REFERENCES diagnostico_plano_acao(id) ON DELETE CASCADE,
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    titulo TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'aberta',
    prazo DATE,
    comentarios TEXT,
    ordem INTEGER NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT diagnostico_plano_subtarefa_ordem_chk CHECK (ordem >= 0)
);

CREATE INDEX IF NOT EXISTS idx_diagnostico_plano_subtarefa_acao
    ON diagnostico_plano_subtarefa(plano_acao_id);

CREATE INDEX IF NOT EXISTS idx_diagnostico_plano_subtarefa_tenant_diag
    ON diagnostico_plano_subtarefa(tenant_id, diagnostico_id);

CREATE TABLE IF NOT EXISTS diagnostico_plano_matriz (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    versao_plano INTEGER NOT NULL DEFAULT 1,
    ordem_exibicao INTEGER NOT NULL,
    departamento TEXT NOT NULL,
    impacto_resumo TEXT NOT NULL,
    criticidade VARCHAR(64) NOT NULL DEFAULT '',
    base_legal TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT diagnostico_plano_matriz_versao_chk CHECK (versao_plano >= 1)
);

CREATE INDEX IF NOT EXISTS idx_diagnostico_plano_matriz_diag
    ON diagnostico_plano_matriz(diagnostico_id, versao_plano);

CREATE TABLE IF NOT EXISTS diagnostico_plano_cronograma (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    versao_plano INTEGER NOT NULL DEFAULT 1,
    ordem_exibicao INTEGER NOT NULL,
    fase TEXT NOT NULL,
    foco TEXT NOT NULL,
    referencia_normativa TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT diagnostico_plano_cronograma_versao_chk CHECK (versao_plano >= 1)
);

CREATE INDEX IF NOT EXISTS idx_diagnostico_plano_cronograma_diag
    ON diagnostico_plano_cronograma(diagnostico_id, versao_plano);

-- RLS (paridade com diagnosticos — tenant via JWT)
ALTER TABLE diagnostico_plano_acao ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_plano_subtarefa ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_plano_matriz ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_plano_cronograma ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagnostico_plano_acao_tenant ON diagnostico_plano_acao;
CREATE POLICY diagnostico_plano_acao_tenant ON diagnostico_plano_acao
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS diagnostico_plano_subtarefa_tenant ON diagnostico_plano_subtarefa;
CREATE POLICY diagnostico_plano_subtarefa_tenant ON diagnostico_plano_subtarefa
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS diagnostico_plano_matriz_tenant ON diagnostico_plano_matriz;
CREATE POLICY diagnostico_plano_matriz_tenant ON diagnostico_plano_matriz
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS diagnostico_plano_cronograma_tenant ON diagnostico_plano_cronograma;
CREATE POLICY diagnostico_plano_cronograma_tenant ON diagnostico_plano_cronograma
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE, DELETE ON diagnostico_plano_acao TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON diagnostico_plano_subtarefa TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON diagnostico_plano_matriz TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON diagnostico_plano_cronograma TO authenticated;
