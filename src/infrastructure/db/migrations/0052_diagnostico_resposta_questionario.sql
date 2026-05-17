-- Respostas do questionário por diagnóstico (normalizado — comparação e evolução entre ciclos).
-- Base: LC 214/2025 (previsibilidade); ABNT NBR 17301:2026 (evidência e rastreabilidade).

CREATE TABLE IF NOT EXISTS diagnostico_resposta_questionario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    ordem_exibicao INTEGER NOT NULL,
    pergunta_id UUID NOT NULL,
    pergunta_codigo VARCHAR(64) NOT NULL,
    dimensao VARCHAR(64) NOT NULL,
    tipo_pergunta VARCHAR(32) NOT NULL,
    texto_pergunta TEXT NOT NULL,
    peso DOUBLE PRECISION NOT NULL,
    base_legal TEXT,
    pilar_abnt TEXT,
    valor_bruto JSONB NOT NULL,
    valor_exibicao TEXT NOT NULL,
    pontuacao_item DOUBLE PRECISION,
    excluida_calculo BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT drq_ordem_chk CHECK (ordem_exibicao >= 0),
    CONSTRAINT drq_peso_chk CHECK (peso >= 0),
    CONSTRAINT drq_pontuacao_chk CHECK (
        pontuacao_item IS NULL OR (pontuacao_item >= 0 AND pontuacao_item <= 100)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_drq_diag_ordem
    ON diagnostico_resposta_questionario (diagnostico_id, ordem_exibicao);

CREATE UNIQUE INDEX IF NOT EXISTS uq_drq_diag_codigo
    ON diagnostico_resposta_questionario (diagnostico_id, pergunta_codigo);

CREATE INDEX IF NOT EXISTS idx_drq_tenant_diag_ordem
    ON diagnostico_resposta_questionario (tenant_id, diagnostico_id, ordem_exibicao);

CREATE INDEX IF NOT EXISTS idx_drq_tenant_codigo
    ON diagnostico_resposta_questionario (tenant_id, pergunta_codigo);

COMMENT ON TABLE diagnostico_resposta_questionario IS
    'QDI — snapshot imutável das respostas do questionário adaptativo por diagnóstico (comparação entre ciclos).';

-- Append-only: evidência de declaração do contribuinte no momento da finalização.
CREATE OR REPLACE FUNCTION qdi_tr_drq_append_only()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'diagnostico_resposta_questionario é append-only (UPDATE/DELETE proibidos)';
END;
$$;

DROP TRIGGER IF EXISTS tr_drq_append_only ON diagnostico_resposta_questionario;
CREATE TRIGGER tr_drq_append_only
    BEFORE UPDATE OR DELETE ON diagnostico_resposta_questionario
    FOR EACH ROW
    EXECUTE FUNCTION qdi_tr_drq_append_only();

ALTER TABLE diagnostico_resposta_questionario ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagnostico_resposta_questionario_tenant ON diagnostico_resposta_questionario;
CREATE POLICY diagnostico_resposta_questionario_tenant ON diagnostico_resposta_questionario
    FOR ALL TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

GRANT SELECT, INSERT ON diagnostico_resposta_questionario TO authenticated;
REVOKE UPDATE, DELETE ON diagnostico_resposta_questionario FROM authenticated;
REVOKE UPDATE, DELETE ON diagnostico_resposta_questionario FROM PUBLIC;
