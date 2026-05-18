import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { clearPendingDiagnosticoFromStorage } from "@/lib/wizard/pending_diagnostico";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";

/** Sinaliza ao wizard que deve ignorar rascunho local (lido em `useLayoutEffect` antes do overlay). */
export const WIZARD_FORCE_NOVO_CICLO_KEY = "qdi_wizard_force_novo_ciclo";

/**
 * Plano avançado: novo ciclo no assistente sem herdar rascunho local nem pendência de gravação.
 * `destino` pode ser `/wizard` ou URL com query de empresa (grelha por CNPJ).
 */
export function navegarRefazerDiagnosticoPainel(
  router: AppRouterInstance,
  destino = "/wizard",
): void {
  clearWizardDraft();
  clearPendingDiagnosticoFromStorage();
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.setItem(WIZARD_FORCE_NOVO_CICLO_KEY, "1");
    } catch {
      /* quota / modo privado */
    }
  }
  router.push(destino);
}

/**
 * Refazer questionário no **mesmo** ciclo: limpa cache local; pré-preenchimento vem da API.
 */
export function navegarRefazerQuestionarioCicloPainel(
  router: AppRouterInstance,
  destino: string,
): void {
  clearWizardDraft();
  clearPendingDiagnosticoFromStorage();
  if (typeof window !== "undefined") {
    try {
      window.sessionStorage.removeItem(WIZARD_FORCE_NOVO_CICLO_KEY);
    } catch {
      /* ignore */
    }
  }
  router.push(destino);
}
