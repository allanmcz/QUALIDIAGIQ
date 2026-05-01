/** @type {import('next').NextConfig} */
const nextConfig = {
  /** Playwright usa porta 3333 (ver playwright.config.ts) — evita bloqueio de origem no dev. */
  allowedDevOrigins: ["127.0.0.1:3333", "localhost:3333"],
};

export default nextConfig;
