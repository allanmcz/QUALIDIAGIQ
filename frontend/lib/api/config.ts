/**
 * URL base da API QualiDiagIQ (rotas `/diagnosticos/...`, etc.).
 *
 * Usar em links e texto — é determinístico no SSR (sem `window`).
 *
 * - Compose web: `NEXT_PUBLIC_API_URL=/api-backend` (produção/BFF) ou deixe o cliente em dev falar
 *   direto com `http://127.0.0.1:60000` (ver `getApiUrlForFetch`).
 * - Sem env, fora das portas de dev com proxy: `http://127.0.0.1:60000` — **não** use `localhost` no macOS
 *   (pode resolver IPv6 `::1` e a porta mapeada pelo Docker falhar com `net::ERR_CONNECTION_REFUSED`).
 */
export function getApiUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://127.0.0.1:60000"
  );
}

/** Portas típicas do Next em dev local (Compose web :60001, Playwright :3333, etc.). */
const PORTAS_DEV_FRONT = new Set(["3000", "3010", "3333", "60001"]);

/** API FastAPI no host quando o mapa Compose expõe `60000:8000` (evita IPv6 `localhost` no macOS). */
const API_HOST_DEV_PADRAO = "http://127.0.0.1:60000";

/**
 * Base para chamadas `fetch` no cliente.
 *
 * Em **`NODE_ENV=development`** no browser, com front em `localhost|127.0.0.1` numa porta de dev
 * acima e `NEXT_PUBLIC_API_URL` ausente, vazio ou `/api-backend`, usa **API direta** em `127.0.0.1:60000`.
 * Evita «Failed to fetch» no painel quando o proxy same-origin (`/api-backend`) falha; a FastAPI já
 * expõe CORS em dev (`CORS_ALLOWED_ORIGINS`) com `Authorization`, `Idempotency-Key`, `X-Rascunho-Token`.
 *
 * Em `next start` / produção mantém-se `NEXT_PUBLIC_API_URL` (ex.: `/api-backend` ou URL absoluta).
 */
export function getApiUrlForFetch(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.trim();

  if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
    const { hostname, port } = window.location;
    const p = port || (window.location.protocol === "https:" ? "443" : "80");
    const frontDevLocal =
      (hostname === "localhost" || hostname === "127.0.0.1") && PORTAS_DEV_FRONT.has(p);
    if (
      frontDevLocal &&
      (!fromEnv || fromEnv === "" || fromEnv === "/api-backend")
    ) {
      return API_HOST_DEV_PADRAO;
    }
  }

  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    const { hostname, port } = window.location;
    const p = port || (window.location.protocol === "https:" ? "443" : "80");
    if ((hostname === "localhost" || hostname === "127.0.0.1") && PORTAS_DEV_FRONT.has(p)) {
      return "/api-backend";
    }
  }
  return API_HOST_DEV_PADRAO;
}

/** Chaves `localStorage` — sessão com conta na plataforma MVP (`/login` → painel). */
export const ADMIN_TOKEN_STORAGE_KEY = "admin_token";
export const ADMIN_NOME_STORAGE_KEY = "admin_nome";
/** E-mail da conta gravado no login/cadastro (pré-preenche respondente no wizard). */
export const ADMIN_EMAIL_STORAGE_KEY = "admin_email";
/** Espelho do claim JWT `perfil_conta` (UX apenas; servidor revalida no POST). */
export const ADMIN_PERFIL_CONTA_STORAGE_KEY = "admin_perfil_conta";

/** JWT salvo pelo fluxo de login MVP (`/login`). */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
}

/**
 * Alinha o href do PDF mock à mesma base que o `fetch` usa (ex.: `/api-backend` no Compose).
 * Evita abrir `http://127.0.0.1:60000/...` quando o browser só alcança a API via proxy same-origin.
 */
export function normalizarHrefRelatorioPdf(url: string | null): string | null {
  if (!url?.trim()) return null;
  const bruto = url.trim();
  if (typeof window === "undefined") return bruto;

  const m = bruto.match(/\/mock-storage\/[0-9a-fA-F-]{36}\/[0-9a-fA-F-]{36}\.pdf/);
  if (!m) return bruto;

  const base = getApiUrlForFetch().replace(/\/$/, "");
  const pathComQuery = m[0];
  if (base.startsWith("/")) {
    return `${window.location.origin}${base}${pathComQuery}`;
  }
  try {
    const parsed = new URL(bruto);
    const port = parsed.port || (parsed.protocol === "https:" ? "443" : "80");
    const devApi =
      (parsed.hostname === "127.0.0.1" || parsed.hostname === "localhost") &&
      (port === "60000" || port === "8000");
    if (devApi) {
      return `${base}${pathComQuery}`;
    }
  } catch {
    return bruto;
  }
  return bruto;
}
