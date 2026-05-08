-- Trilha de anonimização de PII do respondente em diagnóstico finalizado (LGPD).
-- Ampliação controlada do WORM (0025): apenas respondente_email/nome/cargo/telefone → valores sentinelas padronizados.

CREATE TABLE IF NOT EXISTS lgpd_anonimizacao_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    solicitacao_id UUID NULL REFERENCES lgpd_titular_solicitacao (id) ON DELETE SET NULL,
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos (id) ON DELETE CASCADE,
    actor_user_id UUID NULL,
    campos_afetados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_lgpd_anonimizacao_tenant_criado
    ON lgpd_anonimizacao_log (tenant_id, criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_lgpd_anonimizacao_diag
    ON lgpd_anonimizacao_log (diagnostico_id);

COMMENT ON TABLE lgpd_anonimizacao_log IS
    'QDI — auditoria append-only de anonimização de PII do respondente (fluxo LGPD + WORM).';

ALTER TABLE lgpd_anonimizacao_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS lgpd_anon_tenant_insert ON lgpd_anonimizacao_log;
CREATE POLICY lgpd_anon_tenant_insert ON lgpd_anonimizacao_log
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS lgpd_anon_tenant_select ON lgpd_anonimizacao_log;
CREATE POLICY lgpd_anon_tenant_select ON lgpd_anonimizacao_log
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON lgpd_anonimizacao_log TO authenticated;

-- WORM (base 0025): evidência preservada; permite troca explícita de tenant_id para vinculação de lead.
-- Respondente_* só por padrão de anonimização (e-mail sentinel + marcador textual + telefone/remoção de cargo).

CREATE OR REPLACE FUNCTION qdi_tr_block_mutacao_pos_finalizacao()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'finalizado' THEN
        IF OLD.id IS DISTINCT FROM NEW.id
           OR OLD.empresa_cnpj IS DISTINCT FROM NEW.empresa_cnpj
           OR OLD.empresa_razao_social IS DISTINCT FROM NEW.empresa_razao_social
           OR OLD.empresa_porte IS DISTINCT FROM NEW.empresa_porte
           OR OLD.empresa_regime IS DISTINCT FROM NEW.empresa_regime
           OR OLD.empresa_cnae IS DISTINCT FROM NEW.empresa_cnae
           OR OLD.empresa_uf IS DISTINCT FROM NEW.empresa_uf
           OR OLD.empresa_setor_macro IS DISTINCT FROM NEW.empresa_setor_macro
           OR OLD.empresa_faixa_faturamento IS DISTINCT FROM NEW.empresa_faixa_faturamento
           OR OLD.status IS DISTINCT FROM NEW.status
           OR OLD.plano IS DISTINCT FROM NEW.plano
           OR OLD.score_geral IS DISTINCT FROM NEW.score_geral
           OR OLD.criado_em IS DISTINCT FROM NEW.criado_em
           OR OLD.finalizado_em IS DISTINCT FROM NEW.finalizado_em
           OR OLD.hash_sha256 IS DISTINCT FROM NEW.hash_sha256
           OR OLD.score_completo IS DISTINCT FROM NEW.score_completo
           OR OLD.aceite_termos_privacidade_em IS DISTINCT FROM NEW.aceite_termos_privacidade_em
           OR OLD.locale_relatorio IS DISTINCT FROM NEW.locale_relatorio
        THEN
            RAISE EXCEPTION
                'Diagnóstico finalizado: evidência imutável (WORM)';
        END IF;

        IF OLD.respondente_email IS DISTINCT FROM NEW.respondente_email
           OR OLD.respondente_nome IS DISTINCT FROM NEW.respondente_nome
           OR OLD.respondente_cargo IS DISTINCT FROM NEW.respondente_cargo
           OR OLD.respondente_telefone IS DISTINCT FROM NEW.respondente_telefone
        THEN
            IF NOT (
                NEW.respondente_email = (
                    'anon+' || replace(OLD.id::text, '-', '') || '@invalid.qdi'
                )
                AND COALESCE(NEW.respondente_nome, '') = '[anonimizado]'
                AND (
                    NEW.respondente_cargo IS NULL
                    OR BTRIM(NEW.respondente_cargo) = ''
                )
                AND NEW.respondente_telefone IS NULL
            ) THEN
                RAISE EXCEPTION
                    'Diagnóstico finalizado: PII do respondente só pode ser alterada por anonimização LGPD padronizada.';
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION qdi_tr_block_mutacao_pos_finalizacao() IS
    'WORM pós-finalizado: bloqueia mutação de evidência; permite tenant_id (vincular lead) e anonimização respondente padronizada.';
