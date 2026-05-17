/**
 * Timeouts do proxy `/api-backend` → FastAPI.
 *
 * POST `/diagnosticos/` gera PDF + LLM + persistência e costuma exceder 30 s em dev.
 */

export const API_PROXY_TIMEOUT_PADRAO_MS = 30_000;
export const API_PROXY_TIMEOUT_MAX_MS = 300_000;
/** Criação de diagnóstico (painel / self-service / conclusão de rascunho). */
export const API_PROXY_TIMEOUT_DIAGNOSTICO_MS = 180_000;

function lerTimeoutEnv(nome: string, fallback: number): number {
  const bruto =
    typeof process !== "undefined" ? process.env[nome]?.trim() : undefined;
  const n = bruto ? Number.parseInt(bruto, 10) : NaN;
  if (Number.isFinite(n) && n > 0) {
    return Math.min(n, API_PROXY_TIMEOUT_MAX_MS);
  }
  return fallback;
}

export function timeoutProxyMsPadrao(): number {
  return lerTimeoutEnv("API_PROXY_TIMEOUT_MS", API_PROXY_TIMEOUT_PADRAO_MS);
}

function normalizarPathSuffix(pathSuffix: string): string {
  const trimmed = pathSuffix.trim();
  if (!trimmed || trimmed === "/") return "/";
  return trimmed.replace(/\/+$/, "") || "/";
}

/** Rotas cujo upstream pode demorar (PDF, LLM, materialização de plano). */
export function isProxyRotaDiagnosticoLonga(method: string, pathSuffix: string): boolean {
  const m = method.toUpperCase();
  if (m !== "POST") return false;
  const p = normalizarPathSuffix(pathSuffix);
  if (p === "/diagnosticos") return true;
  if (p === "/diagnosticos/self-service") return true;
  if (p.endsWith("/rascunho-self-service/concluir")) return true;
  if (/^\/diagnosticos\/[0-9a-f-]{36}\/retificacao$/i.test(p)) return true;
  return false;
}

export function timeoutProxyMsForRequest(method: string, pathSuffix: string): number {
  if (!isProxyRotaDiagnosticoLonga(method, pathSuffix)) {
    return timeoutProxyMsPadrao();
  }
  const dedicado = lerTimeoutEnv(
    "API_PROXY_TIMEOUT_DIAGNOSTICO_MS",
    API_PROXY_TIMEOUT_DIAGNOSTICO_MS,
  );
  return Math.max(timeoutProxyMsPadrao(), dedicado);
}
