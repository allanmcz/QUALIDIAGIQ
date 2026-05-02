-- Faixa de faturamento bruto anual autodeclarada (opcional) + WORM.

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS empresa_faixa_faturamento VARCHAR(48) NULL;

COMMENT ON COLUMN diagnosticos.empresa_faixa_faturamento IS
    'Faixa anual de faturamento bruto autodeclarada (opcional; segmentação/benchmark). Valores canónicos: ate_360_mil, entre_360_mil_e_4_8_mi, …';

CREATE OR REPLACE FUNCTION qdi_tr_block_mutacao_pos_finalizacao()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'finalizado' THEN
        IF OLD.id IS DISTINCT FROM NEW.id
           OR OLD.tenant_id IS DISTINCT FROM NEW.tenant_id
           OR OLD.respondente_email IS DISTINCT FROM NEW.respondente_email
           OR OLD.respondente_nome IS DISTINCT FROM NEW.respondente_nome
           OR OLD.respondente_cargo IS DISTINCT FROM NEW.respondente_cargo
           OR OLD.respondente_telefone IS DISTINCT FROM NEW.respondente_telefone
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
    END IF;
    RETURN NEW;
END;
$$;
