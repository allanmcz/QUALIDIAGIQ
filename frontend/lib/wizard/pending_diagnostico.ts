/**
 * Payload validado no sessionStorage até gravar: login B2B (POST /diagnosticos/) ou OTP
 * (POST /diagnosticos/self-service após /auth/self-service/token).
 */

import { DiagnosticoPayloadSchema, type DiagnosticoPayload } from "@/lib/schemas/wizard";

export const STORAGE_PENDING_DIAGNOSTICO = "qdi_pending_post_diagnostico_v1";

/** Lê e valida o diagnóstico pendente (mesmo contrato do POST /diagnosticos/). */
export function loadPendingDiagnosticoFromStorage(): DiagnosticoPayload | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);
    if (!raw) return null;
    const data: unknown = JSON.parse(raw);
    const parsed = DiagnosticoPayloadSchema.safeParse(data);
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

/** Remove o diagnóstico pendente após POST bem-sucedido (self-service ou B2B). */
export function clearPendingDiagnosticoFromStorage(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_PENDING_DIAGNOSTICO);
  } catch {
    /* ignore */
  }
}
