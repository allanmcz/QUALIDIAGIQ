-- Alinha senha do admin seed DEV ao formulário de login (admin123).
-- Instalações antigas tinham hash da migração 0004 incompatível com a UI padrão.

UPDATE admins
SET hashed_password = '$2b$12$wMvBNbLK1tmotwrvNSz4rOHkM8F7AQMbMzV6Fdq4h71z1BZVj7Cyi'
WHERE lower(trim(email)) = lower(trim('allan@tributolab.com.br'));
