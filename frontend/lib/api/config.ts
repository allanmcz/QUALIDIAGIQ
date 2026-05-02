/**
 * URL base da API QualiDiagIQ (rotas `/diagnosticos/...`, etc.).
 *
 * Usar em links e texto — é determinístico no SSR (sem `window`).
 *
 * - Compose web: defina `NEXT_PUBLIC_API_URL=/api-backend` + proxy em `next.config.mjs`.
 * - Sem env: `http://127.0.0.1:60000` — **não** use `localhost` no macOS (pode resolver IPv6 `::1` e a porta
 *   mapeada pelo Docker falhar com `net::ERR_CONNECTION_REFUSED`).
 */
export function getApiUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://127.0.0.1:60000"
  );
}

/**
 * Base para chamadas `fetch` no cliente quando o env pode estar desatualizado no bundle.
 * Se a página está em `localhost|127.0.0.1:60001`, força o proxy same-origin `/api-backend`.
 */
export function getApiUrlForFetch(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    const p = port || (window.location.protocol === "https:" ? "443" : "80");
    if (
      (hostname === "localhost" || hostname === "127.0.0.1") &&
      p === "60001"
    ) {
      return "/api-backend";
    }
  }
  return "http://127.0.0.1:60000";
}

const TOKEN_KEY = "admin_token";

/** JWT salvo pelo fluxo de login MVP (`/login`). */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
