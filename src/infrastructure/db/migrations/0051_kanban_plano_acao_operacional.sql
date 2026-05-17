-- Kanban operacional sobre diagnostico_plano_acao (Onda 1.0 — ADR-10 / PLANO_ACAO_V99).
-- Camada auxiliar de workflow; a tabela mestre do plano permanece a fonte da verdade.

CREATE TABLE IF NOT EXISTS diagnostico_plano_acao_estado (
    plano_acao_id UUID PRIMARY KEY
        REFERENCES diagnostico_plano_acao(id)
        ON DELETE CASCADE,
    diagnostico_id UUID NOT NULL
        REFERENCES diagnosticos(id)
        ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    status_execucao VARCHAR(32) NOT NULL DEFAULT 'pendente',
    responsavel_operacional TEXT,
    prazo_operacional DATE,
    bloqueio_motivo TEXT,
    descricao_operacional TEXT,
    ordem_kanban INTEGER NOT NULL DEFAULT 0,
    arquivado BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_dpae_status_execucao CHECK (
        status_execucao IN ('pendente', 'em_andamento', 'bloqueado', 'concluida')
    ),
    CONSTRAINT chk_dpae_ordem_kanban CHECK (ordem_kanban >= 0)
);

CREATE TABLE IF NOT EXISTS diagnostico_plano_acao_comentario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plano_acao_id UUID NOT NULL
        REFERENCES diagnostico_plano_acao(id)
        ON DELETE CASCADE,
    diagnostico_id UUID NOT NULL
        REFERENCES diagnosticos(id)
        ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    autor_label TEXT NOT NULL,
    autor_email TEXT,
    autor_user_id UUID,
    comentario TEXT NOT NULL,
    sha256_payload CHAR(64) NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_dpac_sha256_payload CHECK (
        sha256_payload ~ '^[0-9a-f]{64}$'
    )
);

CREATE INDEX IF NOT EXISTS idx_dpae_tenant_status_ordem
    ON diagnostico_plano_acao_estado (tenant_id, status_execucao, ordem_kanban, plano_acao_id);

CREATE INDEX IF NOT EXISTS idx_dpae_tenant_diag
    ON diagnostico_plano_acao_estado (tenant_id, diagnostico_id);

CREATE INDEX IF NOT EXISTS idx_dpac_tenant_plano_criado
    ON diagnostico_plano_acao_comentario (tenant_id, plano_acao_id, criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_dpac_tenant_diag
    ON diagnostico_plano_acao_comentario (tenant_id, diagnostico_id);

CREATE OR REPLACE FUNCTION qdi_tr_valida_plano_acao_ref()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_tenant_id UUID;
    v_diagnostico_id UUID;
BEGIN
    SELECT tenant_id, diagnostico_id
      INTO v_tenant_id, v_diagnostico_id
      FROM diagnostico_plano_acao
     WHERE id = NEW.plano_acao_id;

    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'plano_acao_id inexistente: %', NEW.plano_acao_id;
    END IF;

    IF NEW.tenant_id IS DISTINCT FROM v_tenant_id THEN
        RAISE EXCEPTION 'tenant_id divergente para plano_acao_id %', NEW.plano_acao_id;
    END IF;

    IF NEW.diagnostico_id IS DISTINCT FROM v_diagnostico_id THEN
        RAISE EXCEPTION 'diagnostico_id divergente para plano_acao_id %', NEW.plano_acao_id;
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION qdi_tr_set_atualizado_em()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.atualizado_em := now();
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION qdi_tr_block_plano_acao_comentario_upd_del()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'diagnostico_plano_acao_comentario e append-only (UPDATE/DELETE proibidos)';
END;
$$;

DROP TRIGGER IF EXISTS tr_dpae_valida_ref ON diagnostico_plano_acao_estado;
CREATE TRIGGER tr_dpae_valida_ref
    BEFORE INSERT OR UPDATE ON diagnostico_plano_acao_estado
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_valida_plano_acao_ref();

DROP TRIGGER IF EXISTS tr_dpac_valida_ref ON diagnostico_plano_acao_comentario;
CREATE TRIGGER tr_dpac_valida_ref
    BEFORE INSERT OR UPDATE ON diagnostico_plano_acao_comentario
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_valida_plano_acao_ref();

DROP TRIGGER IF EXISTS tr_dpae_set_atualizado_em ON diagnostico_plano_acao_estado;
CREATE TRIGGER tr_dpae_set_atualizado_em
    BEFORE UPDATE ON diagnostico_plano_acao_estado
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_set_atualizado_em();

DROP TRIGGER IF EXISTS tr_dpac_append_only ON diagnostico_plano_acao_comentario;
CREATE TRIGGER tr_dpac_append_only
    BEFORE UPDATE OR DELETE ON diagnostico_plano_acao_comentario
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_block_plano_acao_comentario_upd_del();

ALTER TABLE diagnostico_plano_acao_estado ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostico_plano_acao_comentario ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS dpae_tenant_select ON diagnostico_plano_acao_estado;
CREATE POLICY dpae_tenant_select ON diagnostico_plano_acao_estado
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS dpae_tenant_insert ON diagnostico_plano_acao_estado;
CREATE POLICY dpae_tenant_insert ON diagnostico_plano_acao_estado
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS dpae_tenant_update ON diagnostico_plano_acao_estado;
CREATE POLICY dpae_tenant_update ON diagnostico_plano_acao_estado
    FOR UPDATE TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS dpac_tenant_select ON diagnostico_plano_acao_comentario;
CREATE POLICY dpac_tenant_select ON diagnostico_plano_acao_comentario
    FOR SELECT TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

DROP POLICY IF EXISTS dpac_tenant_insert ON diagnostico_plano_acao_comentario;
CREATE POLICY dpac_tenant_insert ON diagnostico_plano_acao_comentario
    FOR INSERT TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT, UPDATE ON diagnostico_plano_acao_estado TO authenticated;
GRANT SELECT, INSERT ON diagnostico_plano_acao_comentario TO authenticated;
REVOKE UPDATE, DELETE ON diagnostico_plano_acao_comentario FROM PUBLIC;
REVOKE UPDATE, DELETE ON diagnostico_plano_acao_comentario FROM authenticated;

INSERT INTO diagnostico_plano_acao_estado (
    plano_acao_id,
    diagnostico_id,
    tenant_id,
    status_execucao,
    responsavel_operacional,
    ordem_kanban,
    criado_em,
    atualizado_em
)
SELECT
    a.id,
    a.diagnostico_id,
    a.tenant_id,
    'pendente',
    NULLIF(a.responsavel_sugerido, ''),
    a.ordem_exibicao,
    now(),
    now()
FROM diagnostico_plano_acao a
ON CONFLICT (plano_acao_id) DO NOTHING;

COMMENT ON TABLE diagnostico_plano_acao_estado IS
    'QDI — Estado operacional Kanban (1:1 com diagnostico_plano_acao). Onda 1.0 V99.';

COMMENT ON TABLE diagnostico_plano_acao_comentario IS
    'QDI — Comentários WORM do Kanban do plano (append-only + sha256_payload).';
