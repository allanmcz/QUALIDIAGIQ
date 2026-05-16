-- Sprint 1 — PDCA + horizonte + criticidade codificada em ``diagnostico_plano_acao``.
-- Base: ABNT NBR 17301:2026 (PDCA); LC 214/2025 (cronograma de transição).

ALTER TABLE diagnostico_plano_acao
    ADD COLUMN IF NOT EXISTS fase_pdca VARCHAR(8) NOT NULL DEFAULT 'DO',
    ADD COLUMN IF NOT EXISTS horizonte_planejado VARCHAR(24) NOT NULL DEFAULT 'CURTO_PRAZO',
    ADD COLUMN IF NOT EXISTS criticidade_codigo VARCHAR(16) NOT NULL DEFAULT 'MEDIA';

ALTER TABLE diagnostico_plano_acao DROP CONSTRAINT IF EXISTS chk_diagnostico_plano_acao_fase_pdca;
ALTER TABLE diagnostico_plano_acao ADD CONSTRAINT chk_diagnostico_plano_acao_fase_pdca CHECK (
    fase_pdca IN ('PLAN', 'DO', 'CHECK', 'ACT')
);

ALTER TABLE diagnostico_plano_acao DROP CONSTRAINT IF EXISTS chk_diagnostico_plano_acao_horizonte;
ALTER TABLE diagnostico_plano_acao ADD CONSTRAINT chk_diagnostico_plano_acao_horizonte CHECK (
    horizonte_planejado IN (
        'IMEDIATO', 'CURTO_PRAZO', 'MEDIO_PRAZO', 'LONGO_PRAZO', 'ESTRATEGICO'
    )
);

ALTER TABLE diagnostico_plano_acao DROP CONSTRAINT IF EXISTS chk_diagnostico_plano_acao_crit_cod;
ALTER TABLE diagnostico_plano_acao ADD CONSTRAINT chk_diagnostico_plano_acao_crit_cod CHECK (
    criticidade_codigo IN ('CRITICA', 'ALTA', 'MEDIA', 'BAIXA')
);

COMMENT ON COLUMN diagnostico_plano_acao.fase_pdca IS
    'Fase PDCA ABNT NBR 17301:2026 (PLAN/DO/CHECK/ACT) — motor Sprint 1.';
COMMENT ON COLUMN diagnostico_plano_acao.horizonte_planejado IS
    'Horizonte temporal LC 214/2025 (IMEDIATO … ESTRATEGICO).';
COMMENT ON COLUMN diagnostico_plano_acao.criticidade_codigo IS
    'Criticidade categórica auditável (CRITICA/ALTA/MEDIA/BAIXA).';
