/**
 * URL base da API QualiDiagIQ (rotas `/diagnosticos/...`, etc.).
 *
 * Usar em links e texto — é determinístico no SSR (sem `window`).
 *
 * - Compose web: defina `NEXT_PUBLIC_API_URL=/api-backend` + proxy em `next.config.mjs`.
 * - Sem env, fora das portas de dev com proxy: `http://127.0.0.1:60000` — **não** use `localhost` no macOS
 *   (pode resolver IPv6 `::1` e a porta mapeada pelo Docker falhar com `net::ERR_CONNECTION_REFUSED`).
 */
export function getApiUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://127.0.0.1:60000"
  );
}

/** Portas típicas de dev Next/Playwright no QDI — mesmo host + `/api-backend` evita CORS (exige `API_PROXY_TARGET` no `next dev`). */
const PORTAS_DEV_PROXY_API_BACKEND = new Set(["3000", "3010", "3333", "60001"]);

/**
 * Base para chamadas `fetch` no cliente quando o env pode estar desatualizado no bundle.
 * Em `localhost|127.0.0.1` nas portas de dev acima, força o proxy same-origin `/api-backend`
 * (alinhado a `allowedDevOrigins` em `next.config.mjs` e CORS da API).
 */
export function getApiUrlForFetch(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    const p = port || (window.location.protocol === "https:" ? "443" : "80");
    if ((hostname === "localhost" || hostname === "127.0.0.1") && PORTAS_DEV_PROXY_API_BACKEND.has(p)) {
      return "/api-backend";
    }
  }
  return "http://127.0.0.1:60000";
}

/** Chaves `localStorage` — fluxo B2B MVP (`/login` → painel). */
export const ADMIN_TOKEN_STORAGE_KEY = "admin_token";
export const ADMIN_NOME_STORAGE_KEY = "admin_nome";

/** JWT salvo pelo fluxo de login MVP (`/login`). */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}
