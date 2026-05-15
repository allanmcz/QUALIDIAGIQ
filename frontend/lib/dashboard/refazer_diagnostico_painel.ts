import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { clearPendingDiagnosticoFromStorage } from "@/lib/wizard/pending_diagnostico";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";

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
  router.push(destino);
}
