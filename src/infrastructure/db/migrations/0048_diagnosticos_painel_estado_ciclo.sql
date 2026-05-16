-- Estado operacional da consultoria no painel — separado do `status` técnico do agregado (WORM granular).
-- Base normativa: rastreio processual LC 214/2025 + ABNT NBR 17301:2026 (gestão complementar ao snapshot).

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS painel_estado_ciclo VARCHAR(32);

UPDATE diagnosticos
SET painel_estado_ciclo = CASE WHEN status = 'finalizado' THEN 'realizado' ELSE 'em_andamento' END
WHERE painel_estado_ciclo IS NULL;

ALTER TABLE diagnosticos ALTER COLUMN painel_estado_ciclo SET NOT NULL;

ALTER TABLE diagnosticos DROP CONSTRAINT IF EXISTS chk_diagnosticos_painel_estado_ciclo;
ALTER TABLE diagnosticos ADD CONSTRAINT chk_diagnosticos_painel_estado_ciclo CHECK (
    painel_estado_ciclo IN ('realizado', 'em_andamento', 'descartado', 'finalizado')
);

COMMENT ON COLUMN diagnosticos.painel_estado_ciclo IS
    'Ciclo de consultoria na UI admin: realizado (entrega), em_andamento, descartado, finalizado (encerramento explícito).';

-- Amplia auditoria append-only de mutações pós-evidência.
ALTER TABLE diagnostico_mutacao_audit DROP CONSTRAINT IF EXISTS chk_dma_tipo;
ALTER TABLE diagnostico_mutacao_audit ADD CONSTRAINT chk_dma_tipo CHECK (
    tipo IN ('m12_likert', 'quadro_implantacao', 'relatorio_pdf', 'painel_estado_ciclo')
);
