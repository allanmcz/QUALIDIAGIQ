/**
 * Modo do assistente quando a sessão é do painel — nova PJ vs. novo ciclo vs. refazer ciclo.
 */

export const WIZARD_QUERY_MODO = "modo";
export const WIZARD_QUERY_DIAGNOSTICO_ID = "diagnostico_id";
export const WIZARD_MODO_NOVO_CICLO = "novo_ciclo";
export const WIZARD_MODO_REFAZER_CICLO = "refazer_ciclo";
export const WIZARD_MODO_NOVA_EMPRESA = "nova_empresa";

export type WizardModoEmpresa =
  | typeof WIZARD_MODO_NOVO_CICLO
  | typeof WIZARD_MODO_REFAZER_CICLO
  | typeof WIZARD_MODO_NOVA_EMPRESA;

/** Lê `modo`, `diagnostico_id` e `empresa_cnpj` da query do browser (client-only). */
export function parseWizardModoEmpresaFromSearchParams(
  sp: URLSearchParams,
): { modo: WizardModoEmpresa; cnpj14: string; razaoSocial: string; diagnosticoId: string } {
  const cnpj14 = sp.get("empresa_cnpj")?.replace(/\D/g, "") ?? "";
  const razaoSocial = sp.get("empresa_razao_social")?.trim() ?? "";
  const diagnosticoId = sp.get(WIZARD_QUERY_DIAGNOSTICO_ID)?.trim() ?? "";
  const modoRaw = sp.get(WIZARD_QUERY_MODO);
  if (modoRaw === WIZARD_MODO_NOVA_EMPRESA) {
    return { modo: WIZARD_MODO_NOVA_EMPRESA, cnpj14, razaoSocial, diagnosticoId };
  }
  if (modoRaw === WIZARD_MODO_REFAZER_CICLO && diagnosticoId.length > 0) {
    return { modo: WIZARD_MODO_REFAZER_CICLO, cnpj14, razaoSocial, diagnosticoId };
  }
  if (modoRaw === WIZARD_MODO_NOVO_CICLO || cnpj14.length === 14) {
    return { modo: WIZARD_MODO_NOVO_CICLO, cnpj14, razaoSocial, diagnosticoId };
  }
  return { modo: WIZARD_MODO_NOVA_EMPRESA, cnpj14: "", razaoSocial: "", diagnosticoId: "" };
}

export function buildWizardUrlNovaEmpresa(): string {
  const q = new URLSearchParams();
  q.set(WIZARD_QUERY_MODO, WIZARD_MODO_NOVA_EMPRESA);
  return `/wizard?${q.toString()}`;
}
