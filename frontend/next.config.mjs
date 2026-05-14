import path from "node:path";
import { fileURLToPath } from "node:url";

import withPWAInit from "@ducanh2912/next-pwa";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Origem da API para CSP `connect-src` em produção (evita «Failed to fetch» quando
 * `NEXT_PUBLIC_API_URL` é http(s) absoluto e não same-origin).
 */
function connectSrcCspParts() {
  const parts = ["'self'", "https:"];
  const api = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (api && (api.startsWith("http://") || api.startsWith("https://"))) {
    try {
      const u = new URL(api);
      const origin = `${u.protocol}//${u.host}`;
      if (!parts.includes(origin)) {
        parts.push(origin);
      }
    } catch {
      /* URL inválida — ignora */
    }
  }
  return parts;
}

/** CSP produção — mesmo valor para ``Content-Security-Policy`` e opcionalmente Report-Only (QDI-H-021). */
function buildProductionCspValue() {
  return [
    "default-src 'self'",
    "img-src 'self' data: https:",
    `connect-src ${connectSrcCspParts().join(" ")}`,
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "worker-src 'self'",
    "manifest-src 'self'",
    "frame-ancestors 'self'",
  ].join("; ");
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  /** Evita aviso «multiple lockfiles» quando existe `package-lock` na home ou na raiz do mono. */
  outputFileTracingRoot: path.join(__dirname, ".."),
  /**
   * Next 14.2+ (block-cross-site): compara só o **hostname** do `Origin` com cada entrada
   * (ex.: Origin `http://127.0.0.1:60001` → hostname `127.0.0.1`). Incluir `127.0.0.1` literal;
   * `127.0.0.1:60001` / URL completa **não** coincidem — ver `csrf-protection.js` / `block-cross-site.js`.
   *
   * Compose publica o web em :60001; Playwright em :3333; `npm run dev` típico em :3010.
   */
  allowedDevOrigins: [
    "127.0.0.1",
    "localhost",
    "::1",
    "127.0.0.1:3000",
    "localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "127.0.0.1:3010",
    "localhost:3010",
    "http://127.0.0.1:3010",
    "http://localhost:3010",
    "127.0.0.1:3333",
    "localhost:3333",
    "http://127.0.0.1:3333",
    "http://localhost:3333",
    "127.0.0.1:60001",
    "localhost:60001",
    "http://127.0.0.1:60001",
    "http://localhost:60001",
  ],
  /**
   * Proxy `/api-backend` → FastAPI: `app/api-backend/[[...slug]]/route.ts` + `API_PROXY_TARGET`.
   * Fase F §F2 modesta — CSP completa deixa para ADR cookie/BFF (.github/adr/ADR-004).
   */
  async headers() {
    const isProd = process.env.NODE_ENV === "production";
    const securityHeaders = [
      { key: "X-Frame-Options", value: "DENY" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "no-referrer" },
      {
        key: "Permissions-Policy",
        value: "geolocation=(), microphone=(), camera=()",
      },
    ];
    if (isProd) {
      const cspValue = buildProductionCspValue();
      securityHeaders.push(
        {
          key: "Strict-Transport-Security",
          value: "max-age=63072000; includeSubDomains; preload",
        },
        { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        {
          key: "Content-Security-Policy",
          value: cspValue,
        },
      );
      if (process.env.QDI_CSP_REPORT_ONLY === "1") {
        securityHeaders.push({
          key: "Content-Security-Policy-Report-Only",
          value: cspValue,
        });
      }
    }
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

/**
 * PWA B2 (Workbox) — ADR-011 Onda 1: SW em produção com exclusões estritas.
 * - Sem SW em `development` ou `CI=true` (Playwright / Actions) — evita flakiness.
 * - ``/api/*``, ``/api-backend/*`` e área autenticada ``/dashboard/*``: **NetworkOnly** (todos os métodos),
 *   para não servir respostas API nem shell do painel a partir de cache offline.
 * - ``navigateFallbackDenylist``: o fallback de documento ``/offline`` não cobre API nem dashboard.
 */
const withPWA = withPWAInit({
  dest: "public",
  disable:
    process.env.NODE_ENV === "development" || process.env.CI === "true",
  register: true,
  extendDefaultRuntimeCaching: true,
  fallbacks: {
    document: "/offline",
  },
  workboxOptions: {
    navigateFallbackDenylist: [
      /^\/api\//,
      /^\/api-backend(\/|$)/,
      /^\/dashboard(\/|$)/,
      /^\/_next\/image/,
    ],
    runtimeCaching: [
      {
        urlPattern: ({ url }) => url.pathname.startsWith("/dashboard"),
        handler: "NetworkOnly",
      },
      {
        urlPattern: ({ url }) => {
          const p = url.pathname;
          return (
            p.startsWith("/api-backend") ||
            p.startsWith("/api/") ||
            (p.startsWith("/_next/data/") && p.includes("api-backend"))
          );
        },
        handler: "NetworkOnly",
      },
    ],
  },
});

export default withPWA(nextConfig);
