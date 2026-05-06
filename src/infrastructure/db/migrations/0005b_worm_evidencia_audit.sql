-- Evidência auditável + imutabilidade pós-finalização (WORM).
-- Base normativa: princípio de auditabilidade e previsibilidade — LC 214/2025 (sistema tributário nacional);
-- rastreabilidade alinhada à ABNT NBR 17301:2026 (gestão de compliance).

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS hash_sha256 CHAR(64);
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS score_completo JSONB;
ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS versao_otimista INTEGER NOT NULL DEFAULT 1;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_status_diagnosticos'
          AND conrelid = 'diagnosticos'::regclass
    ) THEN
        ALTER TABLE diagnosticos ADD CONSTRAINT chk_status_diagnosticos CHECK (
            status IN ('em_andamento', 'finalizado', 'expirado', 'cancelado')
        );
    END IF;
END $$;

CREATE OR REPLACE FUNCTION qdi_tr_block_mutacao_pos_finalizacao()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'finalizado' AND ROW(NEW.*) IS DISTINCT FROM ROW(OLD.*) THEN
        RAISE EXCEPTION
            'Diagnóstico finalizado: evidência imutável (WORM)';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_diagnosticos_worm_update ON diagnosticos;
CREATE TRIGGER tr_diagnosticos_worm_update
    BEFORE UPDATE ON diagnosticos
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_block_mutacao_pos_finalizacao();
