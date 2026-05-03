-- M09 — campo opcional de lead / contato operacional do respondente.
-- M10 — comentários de auditoria sobre a tabela (hardening documental).

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS respondente_telefone VARCHAR(32);

COMMENT ON COLUMN diagnosticos.respondente_telefone IS
  'Telefone opcional do respondente (lead na plataforma). Tratamento conforme política LGPD registrada pelo controlador.';
COMMENT ON TABLE diagnosticos IS
  'Diagnósticos QDI multi-tenant. RLS obrigatória em produção; ver migração 0003_rls_policies.sql.';
