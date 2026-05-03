/**
 * Token opaco devolvido por POST /diagnosticos/rascunho-self-service — referência na BD;
 * guardado no navegador (localStorage) só após clique em «Entrar» porque o redirect OAuth perde o #.
 */

import { migrarChaveDeSessionParaLocalStorage } from "@/lib/wizard/browser_storage_migrate";

export const STORAGE_RASCUNHO_RESGATE_TOKEN = "qdi_rascunho_resgate_token_v1";

export function saveRascunhoResgateTokenParaLogin(token: string): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_RASCUNHO_RESGATE_TOKEN, token.trim());
  } catch {
    /* ignore */
  }
}

export function loadRascunhoResgateToken(): string | null {
  if (typeof window === "undefined") return null;
  migrarChaveDeSessionParaLocalStorage(STORAGE_RASCUNHO_RESGATE_TOKEN);
  try {
    const t = window.localStorage.getItem(STORAGE_RASCUNHO_RESGATE_TOKEN);
    return t != null && t.trim() !== "" ? t.trim() : null;
  } catch {
    return null;
  }
}

export function clearRascunhoResgateToken(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_RASCUNHO_RESGATE_TOKEN);
    window.sessionStorage.removeItem(STORAGE_RASCUNHO_RESGATE_TOKEN);
  } catch {
    /* ignore */
  }
}
