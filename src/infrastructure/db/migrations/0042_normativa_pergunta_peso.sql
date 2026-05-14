-- =====================================================================
-- MIGRATION 0042 — Pesos por pergunta do catálogo (overlay) versionados
-- Produto: QualiDiagIQ (QDI) — M03 transparência / versionamento normativo
-- Base legal: LC 214/2025 (previsibilidade); ABNT NBR 17301:2026 (compliance)
-- Padrão: vigência sobreposta via vigencia_inicio / vigencia_fim (Tributiq)
-- Chave: pergunta_codigo alinhado a ``perguntas_mvp.json`` (ex.: Q-EST-001)
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS qdi;

GRANT USAGE ON SCHEMA qdi TO authenticated, service_role;

CREATE TABLE IF NOT EXISTS qdi.normativa_pergunta_peso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pergunta_codigo TEXT NOT NULL,
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    peso NUMERIC(10, 4) NOT NULL,
    rotulo_versao TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_normativa_pergunta_peso_pos CHECK (peso > 0),
    CONSTRAINT uq_normativa_pergunta_peso_vigencia UNIQUE (pergunta_codigo, vigencia_inicio)
);

CREATE INDEX IF NOT EXISTS idx_normativa_pergunta_peso_vigencia
    ON qdi.normativa_pergunta_peso (pergunta_codigo, vigencia_inicio DESC);

COMMENT ON TABLE qdi.normativa_pergunta_peso IS
    'Overlay de peso por pergunta sobre o catálogo JSON (M03). '
    'Sem linhas: usa-se apenas o JSON; com linhas: DISTINCT ON por código na data.';

ALTER TABLE qdi.normativa_pergunta_peso ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS pol_normativa_pergunta_peso_select ON qdi.normativa_pergunta_peso;
CREATE POLICY pol_normativa_pergunta_peso_select ON qdi.normativa_pergunta_peso
    FOR SELECT TO authenticated
    USING (true);

DROP POLICY IF EXISTS pol_normativa_pergunta_peso_service ON qdi.normativa_pergunta_peso;
CREATE POLICY pol_normativa_pergunta_peso_service ON qdi.normativa_pergunta_peso
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

GRANT SELECT ON TABLE qdi.normativa_pergunta_peso TO authenticated;
GRANT ALL ON TABLE qdi.normativa_pergunta_peso TO service_role;

-- =====================================================================
-- FIM DA MIGRATION 0042
-- =====================================================================
