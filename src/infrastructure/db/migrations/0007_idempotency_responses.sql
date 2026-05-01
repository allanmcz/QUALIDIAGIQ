-- Respostas idempotentes persistidas (POST /diagnosticos/) — sobrevive a restart do processo.
-- LC 214/2025 — previsibilidade das obrigações e operações do contribuinte.

CREATE TABLE IF NOT EXISTS idempotency_responses (
    chave_hash CHAR(64) PRIMARY KEY,
    status_code SMALLINT NOT NULL,
    body BYTEA NOT NULL,
    headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_em TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idempotency_responses_expira ON idempotency_responses (expira_em);
