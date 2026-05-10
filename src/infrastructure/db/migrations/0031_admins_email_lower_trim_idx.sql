-- Índice funcional para lookup de login: ``WHERE lower(trim(email)) = %s``
-- (ver ``buscar_admin_por_email_postgres`` em ``postgres_admin_login.py``).

CREATE INDEX IF NOT EXISTS idx_admins_email_lower_trim ON admins ((lower(trim(email))));
