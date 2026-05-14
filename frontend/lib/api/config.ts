/**
 * URL base da API QualiDiagIQ (rotas `/diagnosticos/...`, etc.).
 *
 * Usar em links e texto — é determinístico no SSR (sem `window`).
 *
 * - Compose web: `NEXT_PUBLIC_API_URL=/api-backend` (proxy same-origin; ver `getApiUrlForFetch`).
 * - Dev sem env: cliente pode usar direto `http://127.0.0.1:60000` (CORS na API necessário).
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
 * Se `NEXT_PUBLIC_API_URL=/api-backend`, o browser **deve** usar esse valor — pedidos same-origin ao Next,
 * que encaminha para a FastAPI (`API_PROXY_TARGET`). Não substituir por `127.0.0.1:60000` no cliente: origens
 * diferentes (ex. `:60001` → `:60000`) exigem CORS e frequentemente aparecem como «Failed to fetch».
 *
 * Com env **ausente ou vazio** em dev local (portas típicas), mantém-se chamada **direta** à API na porta
 * publicada do Compose — útil sem proxy; nesse caso `CORS_ALLOWED_ORIGINS` na API tem de incluir a origem do front.
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
    /** Só força API direta quando **não** há URL pública definida (nunca quando é `/api-backend`). */
    if (frontDevLocal && (!fromEnv || fromEnv === "")) {
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
export const ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY = "admin_token_expires_at";
export const ADMIN_NOME_STORAGE_KEY = "admin_nome";
/** E-mail da conta gravado no login/cadastro (pré-preenche respondente no wizard). */
export const ADMIN_EMAIL_STORAGE_KEY = "admin_email";
/** Espelho do claim JWT `perfil_conta` (UX apenas; servidor revalida no POST). */
export const ADMIN_PERFIL_CONTA_STORAGE_KEY = "admin_perfil_conta";

function decodeBase64UrlJson(segment: string): unknown {
  const normalizado = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalizado.padEnd(Math.ceil(normalizado.length / 4) * 4, "=");
  return JSON.parse(window.atob(padded)) as unknown;
}

function jwtExpiresAtMs(token: string): number | null {
  if (typeof window === "undefined") return null;
  try {
    const payload = decodeBase64UrlJson(token.split(".")[1] ?? "");
    if (!payload || typeof payload !== "object" || !("exp" in payload)) {
      return null;
    }
    const exp = Number((payload as { exp?: unknown }).exp);
    if (!Number.isFinite(exp) || exp <= 0) {
      return null;
    }
    return exp * 1000;
  } catch {
    return null;
  }
}

export function clearPainelSessionStorageOnly(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
  window.localStorage.removeItem(ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY);
  window.localStorage.removeItem(ADMIN_NOME_STORAGE_KEY);
  window.localStorage.removeItem(ADMIN_EMAIL_STORAGE_KEY);
  window.localStorage.removeItem(ADMIN_PERFIL_CONTA_STORAGE_KEY);
}

type PainelSessionStorageInput = {
  token: string;
  nome: string;
  email: string;
  perfilConta: "gratuito" | "avancado";
};

export function persistPainelSessionLocal(input: PainelSessionStorageInput): void {
  if (typeof window === "undefined") return;
  const expiresAt = jwtExpiresAtMs(input.token);
  window.localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, input.token);
  if (expiresAt !== null) {
    window.localStorage.setItem(ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY, String(expiresAt));
  } else {
    window.localStorage.removeItem(ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY);
  }
  window.localStorage.setItem(ADMIN_NOME_STORAGE_KEY, input.nome);
  window.localStorage.setItem(ADMIN_EMAIL_STORAGE_KEY, input.email);
  window.localStorage.setItem(ADMIN_PERFIL_CONTA_STORAGE_KEY, input.perfilConta);
}

/** JWT salvo pelo fluxo de login MVP (`/login`). */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
  if (!token) return null;
  const expiresAtRaw = window.localStorage.getItem(ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY);
  const expiresAt = expiresAtRaw ? Number(expiresAtRaw) : jwtExpiresAtMs(token);
  if (expiresAt && Number.isFinite(expiresAt) && Date.now() >= expiresAt) {
    clearPainelSessionStorageOnly();
    return null;
  }
  if (!expiresAtRaw && expiresAt && Number.isFinite(expiresAt)) {
    window.localStorage.setItem(ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY, String(expiresAt));
  }
  return token;
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
