-- ADR-010 — coluna explícita do algoritmo do hash em admins (argon2id vs bcrypt legado).
-- Rehash gradual no login sem reset obrigatório de senhas.

ALTER TABLE admins
    ADD COLUMN IF NOT EXISTS hash_algoritmo VARCHAR(16) NOT NULL DEFAULT 'bcrypt';

COMMENT ON COLUMN admins.hash_algoritmo IS
    'Algoritmo de hashed_password: bcrypt (legado) ou argon2id (atual). Migração gradual P0-01 / ADR-010.';

CREATE INDEX IF NOT EXISTS idx_admins_hash_algoritmo_legacy
    ON admins (hash_algoritmo)
    WHERE hash_algoritmo = 'bcrypt';
