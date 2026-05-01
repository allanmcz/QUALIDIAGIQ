-- M12 — estado da autoconferência ABNT (10 controles binários), persistido com lock otimista.
-- Compatível com WORM granular (0006): coluna não listada nas mutações bloqueadas — permitido após finalizado.
-- Base normativa: ABNT NBR 17301:2026 (autoconferência operacional); LC 214/2025 (previsibilidade / boa fé).

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS checklist_m12_estado JSONB NULL;

COMMENT ON COLUMN diagnosticos.checklist_m12_estado IS
    'QDI M12 — lista JSON de 10 booleanos (autoconf espelho ABNT NBR 17301:2026); atualização via PATCH com If-Match (versao_otimista).';
