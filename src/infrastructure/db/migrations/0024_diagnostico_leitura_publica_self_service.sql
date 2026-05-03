-- Token opaco de leitura pós-conclusão self-service: permite GET público sem JWT
-- (dados já persistidos em diagnosticos; o token prova posse da sessão de conclusão).

CREATE TABLE IF NOT EXISTS diagnostico_leitura_publica_self_service (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostico_id UUID NOT NULL REFERENCES diagnosticos (id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL,
    token_sha256 CHAR(64) NOT NULL UNIQUE,
    expira_em TIMESTAMPTZ NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dlpss_diag ON diagnostico_leitura_publica_self_service (diagnostico_id);
CREATE INDEX IF NOT EXISTS idx_dlpss_expira ON diagnostico_leitura_publica_self_service (expira_em);

COMMENT ON TABLE diagnostico_leitura_publica_self_service IS
    'QDI — token de leitura única (SHA-256) para página pública pós-OTP self-service; não substitui JWT de painel.';
