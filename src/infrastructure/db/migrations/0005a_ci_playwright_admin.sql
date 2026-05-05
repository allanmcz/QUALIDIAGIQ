-- Admin dedicado ao job Playwright integrado (CI / dev apenas).
-- Senha em texto claro documentada só para pipelines: **secret**
-- Hash gerado com bcrypt (12 rounds); não reutilizar em produção.

INSERT INTO admins (id, email, hashed_password, nome, tenant_id)
VALUES (
    '44444444-4444-4444-a444-444444444444'::uuid,
    'ci-dashboard@qualidiagiq.test',
    '$2b$12$ytZ.GV2rKNGlwPUhzR2hBu3TzrpO6dCLSB2yI56OWt8wNHxrEacmu',
    'Admin CI Playwright',
    '33333333-3333-4333-8333-333333333333'::uuid
)
ON CONFLICT (email) DO NOTHING;
