-- QDI-H-005 — Formato canónico de CNPJ na coluna ``empresa_cnpj`` (14 dígitos ou vazio para lead).
-- Compatível com fluxo sem identificação cadastral (ADR-013).

ALTER TABLE diagnosticos DROP CONSTRAINT IF EXISTS diagnosticos_empresa_cnpj_format_chk;
ALTER TABLE diagnosticos
    ADD CONSTRAINT diagnosticos_empresa_cnpj_format_chk
    CHECK (empresa_cnpj = '' OR empresa_cnpj ~ '^[0-9]{14}$');

COMMENT ON CONSTRAINT diagnosticos_empresa_cnpj_format_chk ON diagnosticos IS
    'CNPJ vazio (lead) ou 14 dígitos numéricos — QDI-H-005.';
