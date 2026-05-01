-- RLS em diagnosticos — isolamento por tenant via claim JWT exposta pelo PostgREST como request.jwt.claims.
-- Compatível com docker local (sem função auth.jwt) e com projeto Supabase hospedado.
-- Login em admins permanece sem RLS nesta fase (ver comentário em _DEVELOPER/ORIENTACAO_CURSOR).

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.qdi_jwt_tenant_id()
RETURNS uuid
LANGUAGE plpgsql
STABLE
SET search_path = public
AS $$
DECLARE
    raw_claims text;
BEGIN
    raw_claims := NULLIF(trim(COALESCE(current_setting('request.jwt.claims', true), '')), '');
    IF raw_claims IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN (raw_claims::jsonb ->> 'tenant_id')::uuid;
EXCEPTION
    WHEN others THEN
        RETURN NULL;
END;
$$;

ALTER TABLE diagnosticos ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS diagnosticos_tenant_select ON diagnosticos;
DROP POLICY IF EXISTS diagnosticos_tenant_insert ON diagnosticos;
DROP POLICY IF EXISTS diagnosticos_tenant_update ON diagnosticos;
DROP POLICY IF EXISTS diagnosticos_tenant_delete ON diagnosticos;
DROP POLICY IF EXISTS diagnosticos_tenant_all ON diagnosticos;

CREATE POLICY diagnosticos_tenant_select ON diagnosticos
    FOR SELECT
    TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

CREATE POLICY diagnosticos_tenant_insert ON diagnosticos
    FOR INSERT
    TO authenticated
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

CREATE POLICY diagnosticos_tenant_update ON diagnosticos
    FOR UPDATE
    TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id())
    WITH CHECK (tenant_id = public.qdi_jwt_tenant_id());

CREATE POLICY diagnosticos_tenant_delete ON diagnosticos
    FOR DELETE
    TO authenticated
    USING (tenant_id = public.qdi_jwt_tenant_id());

GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE diagnosticos TO authenticated;
