-- IP de origem do respondente (LGPD — anonimização J2).
-- Amplia o WORM de 0029: PII do respondente inclui respondente_ip_origem (NULL após anonimização).

ALTER TABLE diagnosticos
    ADD COLUMN IF NOT EXISTS respondente_ip_origem VARCHAR(45) NULL;

COMMENT ON COLUMN diagnosticos.respondente_ip_origem IS
    'Melhor esforço do IP da camada HTTP (IPv4/IPv6 até 45 chars); NULL após anonimização LGPD padronizada.';

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
           OR OLD.respondente_ip_origem IS DISTINCT FROM NEW.respondente_ip_origem
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
                AND NEW.respondente_ip_origem IS NULL
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
    'WORM pós-finalizado: bloqueia mutação de evidência; permite tenant_id (vincular lead) e anonimização respondente padronizada (inclui IP).';
