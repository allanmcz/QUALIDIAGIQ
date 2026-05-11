/**
 * Payload legado no navegador (localStorage) até POST /diagnosticos/ com JWT após login.
 * Fluxo principal sem sessão: **POST /diagnosticos/rascunho-self-service** + token na BD.
 */

import {
  DiagnosticoPayloadArmazenadoSchema,
  type DiagnosticoPayloadArmazenado,
} from "@/lib/schemas/wizard";

import { migrarChaveDeSessionParaLocalStorage } from "@/lib/wizard/browser_storage_migrate";

export const STORAGE_PENDING_DIAGNOSTICO = "qdi_pending_post_diagnostico_v1";

/** Resultado da leitura do pendente — distingue ausência, JSON inválido e schema inválido. */
export type PendingDiagnosticoStorageResult =
  | { ok: true; data: DiagnosticoPayloadArmazenado }
  | { ok: false; reason: "missing" | "invalid_json" | "invalid_schema" };

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

/**
 * Lê e valida o diagnóstico pendente com o schema **armazenado** (sem regra ADR-013 de sessão).
 * O envio com JWT ao painel continua sujeito a `DiagnosticoPayloadSchema` / API.
 */
export function parsePendingDiagnosticoFromStorage(): PendingDiagnosticoStorageResult {
  if (typeof window === "undefined") {
    return { ok: false, reason: "missing" };
  }
  migrarChaveDeSessionParaLocalStorage(STORAGE_PENDING_DIAGNOSTICO);
  try {
    const raw = window.localStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);
    if (!raw?.trim()) return { ok: false, reason: "missing" };
    let data: unknown;
    try {
      data = JSON.parse(raw);
    } catch {
      return { ok: false, reason: "invalid_json" };
    }
    const parsed = DiagnosticoPayloadArmazenadoSchema.safeParse(data);
    if (!parsed.success) return { ok: false, reason: "invalid_schema" };
    return { ok: true, data: parsed.data };
  } catch {
    return { ok: false, reason: "invalid_json" };
  }
}

/** Retorna o pendente válido ou `null` (ausência / JSON ou schema inválidos). */
export function loadPendingDiagnosticoFromStorage(): DiagnosticoPayloadArmazenado | null {
  const r = parsePendingDiagnosticoFromStorage();
  return r.ok ? r.data : null;
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
