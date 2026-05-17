/**
 * Idempotency-Key estável por tentativa de envio no assistente (painel).
 *
 * Se o proxy expirar após a API ter gravado, o reenvio com a mesma chave devolve o mesmo 201
 * (middleware de idempotência na FastAPI) em vez de duplicar diagnóstico.
 */

const STORAGE_KEY = "qdi_wizard_post_diagnostico_idempotency_v1";

export function obterIdempotencyKeyPostDiagnostico(): string {
  if (typeof window === "undefined") {
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
  try {
    const existente = window.sessionStorage.getItem(STORAGE_KEY)?.trim();
    if (existente) return existente;
    const nova =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    window.sessionStorage.setItem(STORAGE_KEY, nova);
    return nova;
  } catch {
    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }
}

export function limparIdempotencyKeyPostDiagnostico(): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}
