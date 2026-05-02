-- Seed opcional para DEV — senha conhecida apenas em ambiente local; produção: src/scripts/criar_admin.py
INSERT INTO admins (email, hashed_password, nome, tenant_id)
VALUES (
    'allan@tributolab.com.br',
    '$2b$12$wMvBNbLK1tmotwrvNSz4rOHkM8F7AQMbMzV6Fdq4h71z1BZVj7Cyi',
    'Admin Tributiq',
    '33333333-3333-4333-8333-333333333333'::uuid
)
ON CONFLICT (email) DO NOTHING;
