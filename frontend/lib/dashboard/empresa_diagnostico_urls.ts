/**
 * Rotas do painel — agrupamento por PJ (CNPJ) e atalho para novo ciclo no wizard.
 */

/** Extrai 14 dígitos do segmento de URL `/dashboard/empresas/[cnpj]`. */
export function parseCnpjFromRouteSegment(segment: string): string | null {
  const decoded = decodeURIComponent(segment).replace(/\D/g, "");
  return decoded.length === 14 ? decoded : null;
}

/** Monta `/wizard` com query para pré-preencher passo 1 (sessão painel + ADR-013). */
export function buildWizardUrlNovaDiagnosticoEmpresa(cnpj14: string, razaoSocial: string): string {
  const q = new URLSearchParams();
  q.set("empresa_cnpj", cnpj14.replace(/\D/g, ""));
  const r = razaoSocial.trim();
  if (r.length >= 3) {
    q.set("empresa_razao_social", r);
  }
  return `/wizard?${q.toString()}`;
}

/** Path da grelha de diagnósticos da empresa (CNPJ só dígitos). */
export function buildEmpresaDiagnosticosHref(cnpj14: string, razaoSocial: string): string {
  const c = cnpj14.replace(/\D/g, "");
  const base = `/dashboard/empresas/${c}`;
  const r = razaoSocial.trim();
  if (r.length < 3) return base;
  return `${base}?razao_social=${encodeURIComponent(r)}`;
}
