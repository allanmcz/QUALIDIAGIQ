-- QDI-H-019 — Índices compostos para listagens por tenant (painel / relatórios).

CREATE INDEX IF NOT EXISTS idx_diagnosticos_tenant_criado_desc
    ON diagnosticos (tenant_id, criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_diagnosticos_tenant_cnpj_finalizado_desc
    ON diagnosticos (tenant_id, empresa_cnpj, finalizado_em DESC NULLS LAST);

COMMENT ON INDEX idx_diagnosticos_tenant_criado_desc IS
    'Listagem cronológica por tenant (QDI-H-019).';
