-- M10 — Documentação no catálogo (COMMENT) das políticas RLS e da função de tenant (runbook).
-- Não altera comportamento — apenas auditoria humana para operação e segurança.
-- LC 214/2025 art. 5º (previsibilidade) + ABNT NBR 17301:2026 (rastreabilidade).

COMMENT ON FUNCTION public.qdi_jwt_tenant_id() IS
    'QDI multi-tenant: extrai UUID tenant_id das claims JWT (setting request.jwt.claims). Usado pelas políticas RLS em diagnosticos.';

COMMENT ON POLICY diagnosticos_tenant_select ON public.diagnosticos IS
    'RLS SELECT: apenas linhas com tenant_id igual ao JWT (role authenticated).';

COMMENT ON POLICY diagnosticos_tenant_insert ON public.diagnosticos IS
    'RLS INSERT WITH CHECK: tenant_id deve coincidir com o tenant do JWT (role authenticated).';

COMMENT ON POLICY diagnosticos_tenant_update ON public.diagnosticos IS
    'RLS UPDATE USING/WITH CHECK: isolamento estrito por tenant_id do JWT (role authenticated).';

COMMENT ON POLICY diagnosticos_tenant_delete ON public.diagnosticos IS
    'RLS DELETE: somente registros do tenant corrente (role authenticated).';
