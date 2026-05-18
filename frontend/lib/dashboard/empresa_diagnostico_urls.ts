/**
 * Rotas do painel — agrupamento por PJ (CNPJ) e atalho para novo ciclo no wizard.
 */

import {
  WIZARD_MODO_NOVO_CICLO,
  WIZARD_MODO_REFAZER_CICLO,
  WIZARD_QUERY_DIAGNOSTICO_ID,
  WIZARD_QUERY_MODO,
} from "@/lib/wizard/wizard_modo_empresa";

/** Extrai 14 dígitos do segmento de URL `/dashboard/empresas/[cnpj]`. */
export function parseCnpjFromRouteSegment(segment: string): string | null {
  let raw = segment;
  try {
    raw = decodeURIComponent(segment);
  } catch {
    /* Segmento com sequência % inválida — evita URIError → 500 no Server Component */
    raw = segment;
  }
  const decoded = raw.replace(/\D/g, "");
  return decoded.length === 14 ? decoded : null;
}

/** Monta `/wizard` com query para pré-preencher passo 1 (sessão painel + ADR-013). */
export function buildWizardUrlNovaDiagnosticoEmpresa(cnpj14: string, razaoSocial: string): string {
  const q = new URLSearchParams();
  q.set(WIZARD_QUERY_MODO, WIZARD_MODO_NOVO_CICLO);
  q.set("empresa_cnpj", cnpj14.replace(/\D/g, ""));
  const r = razaoSocial.trim();
  if (r.length >= 3) {
    q.set("empresa_razao_social", r);
  }
  return `/wizard?${q.toString()}`;
}

/** Assistente para refazer o questionário do **mesmo** ciclo (`diagnostico_id`). */
export function buildWizardUrlRefazerQuestionarioCiclo(
  cnpj14: string,
  razaoSocial: string,
  diagnosticoId: string,
): string {
  const q = new URLSearchParams();
  q.set(WIZARD_QUERY_MODO, WIZARD_MODO_REFAZER_CICLO);
  q.set(WIZARD_QUERY_DIAGNOSTICO_ID, diagnosticoId);
  q.set("empresa_cnpj", cnpj14.replace(/\D/g, ""));
  const r = razaoSocial.trim();
  if (r.length >= 3) {
    q.set("empresa_razao_social", r);
  }
  return `/wizard?${q.toString()}`;
}

/** Query `?expand=` — ciclo com linha expandida na vista unificada por CNPJ. */
export const QUERY_EXPAND_DIAGNOSTICO = "expand";

type EmpresaDiagnosticosHrefOpts = {
  /** Abre a linha expandida na grelha (M05, M12, etc.). */
  expandDiagnosticoId?: string;
  /** Âncora no painel expandido (ex.: `empresa-m12-autoconf`). */
  hash?: string;
};

/** Atalho para um ciclo na página canónica da empresa (`/dashboard/empresas/{cnpj}`). */
export function buildEmpresaHrefCiclo(
  cnpj14: string,
  razaoSocial: string,
  diagnosticoId: string,
  opts?: Pick<EmpresaDiagnosticosHrefOpts, "hash">,
): string {
  return buildEmpresaDiagnosticosHref(cnpj14, razaoSocial, {
    expandDiagnosticoId: diagnosticoId,
    hash: opts?.hash,
  });
}

/** Path da grelha de diagnósticos da empresa (CNPJ só dígitos). */
export function buildEmpresaDiagnosticosHref(
  cnpj14: string,
  razaoSocial: string,
  opts?: EmpresaDiagnosticosHrefOpts,
): string {
  const c = cnpj14.replace(/\D/g, "");
  const base = `/dashboard/empresas/${c}`;
  const q = new URLSearchParams();
  const r = razaoSocial.trim();
  if (r.length >= 3) {
    q.set("razao_social", r);
  }
  if (opts?.expandDiagnosticoId) {
    q.set(QUERY_EXPAND_DIAGNOSTICO, opts.expandDiagnosticoId);
  }
  const qs = q.toString();
  const path = qs ? `${base}?${qs}` : base;
  const hash = opts?.hash?.replace(/^#/, "").trim();
  return hash ? `${path}#${hash}` : path;
}
