-- Lotes de respostas por refazer questionário no mesmo ciclo (WORM na linha do diagnóstico).
-- Base: ADR-012 (retificação append-only) + evidência versionada por pergunta.

ALTER TABLE diagnostico_resposta_questionario
    ADD COLUMN IF NOT EXISTS refazer_lote SMALLINT NOT NULL DEFAULT 1;

COMMENT ON COLUMN diagnostico_resposta_questionario.refazer_lote IS
    '1 = snapshot da finalização original; 2+ = refazer questionário no mesmo diagnostico_id.';

DROP INDEX IF EXISTS uq_drq_diag_codigo;
DROP INDEX IF EXISTS uq_drq_diag_ordem;

CREATE UNIQUE INDEX IF NOT EXISTS uq_drq_diag_codigo_lote
    ON diagnostico_resposta_questionario (diagnostico_id, pergunta_codigo, refazer_lote);

CREATE UNIQUE INDEX IF NOT EXISTS uq_drq_diag_ordem_lote
    ON diagnostico_resposta_questionario (diagnostico_id, ordem_exibicao, refazer_lote);
