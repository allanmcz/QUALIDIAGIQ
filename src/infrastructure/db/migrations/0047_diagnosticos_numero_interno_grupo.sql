-- Numeracao interna por tenant para listagens do painel (sem substituir o UUID tecnico na API).
-- Regra: sequencial dentro do grupo empresa_cnpj preenchido (14 digitos ou texto validado); se CNPJ vazio,
-- sequencial dentro do mesmo e-mail normalizado do respondente (LGPD lead / auto-preenchido).
--
-- Base: ordem cronologica `criado_em` ASC dentro de cada grupo; valores atribuidos ao INSERT via trigger.

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS numero_interno_grupo INTEGER;

COMMENT ON COLUMN diagnosticos.numero_interno_grupo IS
    'Sequencial por tenant e grupo empresa (CNPJ ou e-mail quando CNPJ vazio); UX em grelhas do painel.';

-- Retroactividade para bases ja populadas (mesma regra do trigger).
WITH ranked AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY tenant_id,
                   CASE
                       WHEN NULLIF(trim(empresa_cnpj), '') IS NOT NULL THEN 'c:' || trim(empresa_cnpj)
                       ELSE 'e:' || lower(trim(coalesce(respondente_email, '')))
                   END
               ORDER BY criado_em ASC NULLS LAST, id ASC
           ) AS n
    FROM diagnosticos
)
UPDATE diagnosticos AS d
SET numero_interno_grupo = ranked.n
FROM ranked
WHERE d.id = ranked.id;

ALTER TABLE diagnosticos ALTER COLUMN numero_interno_grupo SET NOT NULL;

CREATE OR REPLACE FUNCTION qdi_diag_assign_numero_interno_grupo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    gchave TEXT;
    prox INTEGER;
BEGIN
    IF NEW.empresa_cnpj IS NOT NULL AND trim(NEW.empresa_cnpj) <> '' THEN
        gchave := 'c:' || trim(NEW.empresa_cnpj);
    ELSE
        gchave := 'e:' || lower(trim(coalesce(NEW.respondente_email, '')));
    END IF;

    PERFORM pg_advisory_xact_lock(hashtext(NEW.tenant_id::TEXT || '|' || gchave));

    SELECT COALESCE(MAX(numero_interno_grupo), 0) + 1
    INTO prox
    FROM diagnosticos
    WHERE tenant_id = NEW.tenant_id
      AND (
          (trim(coalesce(NEW.empresa_cnpj, '')) <> ''
              AND trim(empresa_cnpj) = trim(NEW.empresa_cnpj))
          OR
          (trim(coalesce(NEW.empresa_cnpj, '')) = ''
              AND trim(coalesce(empresa_cnpj, '')) = ''
              AND lower(trim(coalesce(respondente_email, '')))
                  = lower(trim(coalesce(NEW.respondente_email, ''))))
      );

    NEW.numero_interno_grupo := prox;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS tr_diag_numero_interno_grupo ON diagnosticos;

CREATE TRIGGER tr_diag_numero_interno_grupo
    BEFORE INSERT ON diagnosticos
    FOR EACH ROW
    EXECUTE FUNCTION qdi_diag_assign_numero_interno_grupo();

COMMENT ON FUNCTION qdi_diag_assign_numero_interno_grupo() IS
    'Define numero_interno_grupo no INSERT por tenant + CNPJ (nao vazio) ou mail respondente quando CNPJ vazio.';
