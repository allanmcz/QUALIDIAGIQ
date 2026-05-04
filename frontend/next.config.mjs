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

/** @type {import('next').NextConfig} */
const nextConfig = {
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
      { key: "X-Frame-Options", value: "SAMEORIGIN" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      {
        key: "Permissions-Policy",
        value:
          "camera=(), microphone=(), geolocation=(), payment=(), interest-cohort=()",
      },
    ];
    if (isProd) {
      securityHeaders.push(
        {
          key: "Strict-Transport-Security",
          value: "max-age=63072000; includeSubDomains; preload",
        },
        { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        {
          key: "Content-Security-Policy",
          value: [
            "default-src 'self'",
            "img-src 'self' data: https:",
            `connect-src ${connectSrcCspParts().join(" ")}`,
            "script-src 'self' 'unsafe-inline'",
            "style-src 'self' 'unsafe-inline'",
            "frame-ancestors 'self'",
          ].join("; "),
        },
      );
    }
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
