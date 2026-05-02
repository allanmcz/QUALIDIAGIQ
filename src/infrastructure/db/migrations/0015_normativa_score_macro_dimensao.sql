-- =====================================================================
-- MIGRATION 0015 — Pesos macro por dimensão (score geral) versionados
-- Produto: QualiDiagIQ (QDI) — Épico E1 (PLANO_EXECUCAO_EPICOS_GRANDES_QDI.md)
-- Base legal: LC 214/2025 (previsibilidade); ABNT NBR 17301:2026 (compliance)
-- Padrão: vigência sobreposta via vigencia_inicio / vigencia_fim (Tributiq)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS qdi;

GRANT USAGE ON SCHEMA qdi TO authenticated, service_role;

CREATE TABLE IF NOT EXISTS qdi.normativa_score_macro_dimensao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    dimensao TEXT NOT NULL,
    peso NUMERIC(8, 4) NOT NULL,
    rotulo_versao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_normativa_score_macro_peso_pos CHECK (peso > 0),
    CONSTRAINT chk_normativa_score_macro_dimensao CHECK (dimensao IN (
        'fiscal',
        'estrategica',
        'contabil',
        'financeira',
        'operacional',
        'tecnologica',
        'compliance_abnt_17301'
    )),
    CONSTRAINT uq_normativa_score_macro_dim_vigencia UNIQUE (dimensao, vigencia_inicio)
);

CREATE INDEX IF NOT EXISTS idx_normativa_score_macro_vigencia
    ON qdi.normativa_score_macro_dimensao (vigencia_inicio DESC);

COMMENT ON TABLE qdi.normativa_score_macro_dimensao IS
    'Pesos macro por dimensão para agregação do score geral (M03). '
    'Versionado por vigência; DISTINCT ON no serviço resolve a linha efetiva por data.';

ALTER TABLE qdi.normativa_score_macro_dimensao ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_normativa_score_macro_select ON qdi.normativa_score_macro_dimensao;
CREATE POLICY pol_normativa_score_macro_select ON qdi.normativa_score_macro_dimensao
    FOR SELECT TO authenticated
    USING (true);

DROP POLICY IF EXISTS pol_normativa_score_macro_service ON qdi.normativa_score_macro_dimensao;
CREATE POLICY pol_normativa_score_macro_service ON qdi.normativa_score_macro_dimensao
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

GRANT SELECT ON TABLE qdi.normativa_score_macro_dimensao TO authenticated;
GRANT ALL ON TABLE qdi.normativa_score_macro_dimensao TO service_role;

-- Baseline espelhando PESOS_MACRO_DIMENSAO_SCORE_GERAL (domain) — vigência a partir de 2026-01-01
INSERT INTO qdi.normativa_score_macro_dimensao (
    vigencia_inicio, vigencia_fim, dimensao, peso, rotulo_versao
) VALUES
    ('2026-01-01', NULL, 'fiscal', 1.5, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'tecnologica', 1.3, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'compliance_abnt_17301', 1.2, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'estrategica', 1.0, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'contabil', 1.0, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'financeira', 1.0, 'baseline-m03-qdi-2026'),
    ('2026-01-01', NULL, 'operacional', 1.0, 'baseline-m03-qdi-2026')
ON CONFLICT (dimensao, vigencia_inicio) DO NOTHING;

-- =====================================================================
-- FIM DA MIGRATION 0015
-- =====================================================================
