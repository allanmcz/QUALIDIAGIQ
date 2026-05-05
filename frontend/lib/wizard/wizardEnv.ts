/**
 * Feature flags e leituras de ambiente específicas do wizard (Next.js).
 */

/** Painel P8 (POST /normativa/validar-ancora). Colchetes em `process.env` evitam substituição estática no bundle em `next dev` quando o Playwright injeta `NEXT_PUBLIC_WIZARD_NORMATIVA`. */
export function normativaWizardPainelAtivo(): boolean {
  return process.env["NEXT_PUBLIC_WIZARD_NORMATIVA"] === "true";
}
