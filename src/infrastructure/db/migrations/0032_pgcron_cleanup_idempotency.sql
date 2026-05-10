-- Limpeza periódica de idempotency_responses expirados (LC 214/2025 — previsibilidade).
-- Preferência: pg_cron a cada 4h. Fallback operacional: função SQL + POST /admin/maintenance/cleanup-idempotency.

CREATE OR REPLACE FUNCTION qdi_cleanup_idempotency()
RETURNS TABLE(deleted_count bigint, executed_at timestamptz)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    cnt bigint;
BEGIN
    WITH del AS (
        DELETE FROM idempotency_responses
        WHERE expira_em < now()
        RETURNING 1
    )
    SELECT count(*) INTO cnt FROM del;

    RETURN QUERY SELECT cnt, clock_timestamp();
END;
$$;

COMMENT ON FUNCTION qdi_cleanup_idempotency() IS
    'QDI — Remove linhas expiradas de idempotency_responses. Usada por pg_cron ou endpoint admin.';

-- pg_cron (opcional — indisponível em imagens Docker CI sem pacote; falha silenciosa).
DO $$
DECLARE
    jid bigint;
BEGIN
    CREATE EXTENSION IF NOT EXISTS pg_cron;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Extensão pg_cron indisponível neste cluster: %', SQLERRM;
END;
$$;

DO $$
DECLARE
    jid bigint;
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
        FOR jid IN SELECT jobid FROM cron.job WHERE jobname = 'qdi-cleanup-idempotency'
        LOOP
            PERFORM cron.unschedule(jid);
        END LOOP;
        PERFORM cron.schedule(
            'qdi-cleanup-idempotency',
            '0 */4 * * *',
            'DELETE FROM idempotency_responses WHERE expira_em < now()'
        );
        RAISE NOTICE 'Job pg_cron qdi-cleanup-idempotency agendado (4h).';
    END IF;
EXCEPTION WHEN undefined_table THEN
    RAISE NOTICE 'Schema cron ausente — ignorando agendamento pg_cron.';
WHEN OTHERS THEN
    RAISE NOTICE 'Agendamento pg_cron não aplicado: %', SQLERRM;
END;
$$;
