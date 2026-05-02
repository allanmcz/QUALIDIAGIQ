/** Alvo interno do proxy (servidor Next → FastAPI). Compose: http://api:8000 */
const apiProxyTarget = process.env.API_PROXY_TARGET?.trim();

/** @type {import('next').NextConfig} */
const nextConfig = {
  /**
   * Playwright usa baseURL http://127.0.0.1:3333 (ver playwright.config.ts).
   * Next 14+ pode exigir origem explícita para assets `/_next/*` em dev.
   */
  allowedDevOrigins: [
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
   * Mesmo host que o browser → sem CORS. O cliente usa NEXT_PUBLIC_API_URL=/api-backend;
   * o Node encaminha para API_PROXY_TARGET (rede Docker).
   */
  async rewrites() {
    if (!apiProxyTarget) return [];
    const base = apiProxyTarget.replace(/\/$/, "");
    return [{ source: "/api-backend/:path*", destination: `${base}/:path*` }];
  },
  /** Fase F §F2 modesta — CSP completa deixa para ADR cookie/BFF (.github/adr/ADR-004). */
  async headers() {
    const isProd = process.env.NODE_ENV === "production";
    const securityHeaders = [
      { key: "X-Frame-Options", value: "SAMEORIGIN" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      {
        key: "Permissions-Policy",
        value: "camera=(), microphone=(), geolocation=(), payment=()",
      },
    ];
    if (isProd) {
      securityHeaders.push({
        key: "Strict-Transport-Security",
        value: "max-age=63072000; includeSubDomains; preload",
      });
    }
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
