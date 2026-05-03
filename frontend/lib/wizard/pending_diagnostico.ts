/**
 * Payload legado no navegador (localStorage) até POST /diagnosticos/ com JWT após login.
 * Fluxo principal sem sessão: **POST /diagnosticos/rascunho-self-service** + token na BD.
 */

import { DiagnosticoPayloadSchema, type DiagnosticoPayload } from "@/lib/schemas/wizard";

import { migrarChaveDeSessionParaLocalStorage } from "@/lib/wizard/browser_storage_migrate";

export const STORAGE_PENDING_DIAGNOSTICO = "qdi_pending_post_diagnostico_v1";

/** Indica se existe payload pendente (pós-login / migração). */
export function hasPendingDiagnosticoInBrowser(): boolean {
  if (typeof window === "undefined") return false;
  migrarChaveDeSessionParaLocalStorage(STORAGE_PENDING_DIAGNOSTICO);
  try {
    const raw = window.localStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);
    return raw != null && raw.trim() !== "";
  } catch {
    return false;
  }
}

/** Lê e valida o diagnóstico pendente (mesmo contrato do POST /diagnosticos/). */
export function loadPendingDiagnosticoFromStorage(): DiagnosticoPayload | null {
  if (typeof window === "undefined") return null;
  migrarChaveDeSessionParaLocalStorage(STORAGE_PENDING_DIAGNOSTICO);
  try {
    const raw = window.localStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);
    if (!raw) return null;
    const data: unknown = JSON.parse(raw);
    const parsed = DiagnosticoPayloadSchema.safeParse(data);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

/** Remove o diagnóstico pendente após POST bem-sucedido (self-service ou conta na plataforma). */
export function clearPendingDiagnosticoFromStorage(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_PENDING_DIAGNOSTICO);
    window.sessionStorage.removeItem(STORAGE_PENDING_DIAGNOSTICO);
  } catch {
    /* ignore */
  }
}
