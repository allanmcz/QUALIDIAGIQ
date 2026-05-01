/** @type {import('next').NextConfig} */
const nextConfig = {
  /** Playwright usa porta 3333 (ver playwright.config.ts) — evita bloqueio de origem no dev. */
  allowedDevOrigins: ["127.0.0.1:3333", "localhost:3333"],
  /** Fase F §F2 modesta — CSP completa deixa para ADR cookie/BFF (.github/adr/ADR-004). */
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },
};

export default nextConfig;
