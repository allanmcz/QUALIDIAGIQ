-- Perfil comercial do admin na plataforma (claim JWT `perfil_conta`) — MVP dev.
-- gratuito: diagnósticos apenas plano gratuito (servidor impõe).
-- avancado: pode gravar diagnóstico avançado (todas as visões do motor previstas para esse plano).

ALTER TABLE admins ADD COLUMN IF NOT EXISTS perfil_conta VARCHAR(20) NOT NULL DEFAULT 'gratuito';

UPDATE admins
SET perfil_conta = 'avancado'
WHERE lower(trim(email)) = lower(trim('allan@tributolab.com.br'));

-- Conta gratuita (tenant isolado do consultor pago).
-- Senha: amma2804 — bcrypt 12 rounds (ambiente local apenas; não reutilizar em produção).
INSERT INTO admins (email, hashed_password, nome, tenant_id, perfil_conta)
VALUES (
    'allanmcz@gmail.com',
    '$2b$12$jhwkymcHJyZVWWc87B5kzeyjvGb9DEePWJPGKc4T7qmr3YU40VAAC',
    'Allan MCZ',
    '55555555-5555-4555-8555-555555555555'::uuid,
    'gratuito'
)
ON CONFLICT (email) DO UPDATE SET
    hashed_password = EXCLUDED.hashed_password,
    nome = EXCLUDED.nome,
    tenant_id = EXCLUDED.tenant_id,
    perfil_conta = EXCLUDED.perfil_conta;
