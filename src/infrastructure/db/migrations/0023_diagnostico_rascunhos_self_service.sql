-- Rascunho de diagnóstico self-service: payload na BD até OTP ou vinculação à conta (sem depender do sessionStorage como etapa final).

CREATE TABLE IF NOT EXISTS diagnostico_rascunhos_self_service (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    email_norm VARCHAR(320) NOT NULL,
    payload_json JSONB NOT NULL,
    token_sha256 CHAR(64) NOT NULL UNIQUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira_em TIMESTAMPTZ NOT NULL,
    consumido_em TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_drss_email_norm ON diagnostico_rascunhos_self_service (email_norm);
CREATE INDEX IF NOT EXISTS idx_drss_expira_ativo
    ON diagnostico_rascunhos_self_service (expira_em)
    WHERE consumido_em IS NULL;

COMMENT ON TABLE diagnostico_rascunhos_self_service IS
    'QDI — payload do assistente antes da prova OTP ou vinculação JWT; token opaco (SHA-256 na coluna).';
