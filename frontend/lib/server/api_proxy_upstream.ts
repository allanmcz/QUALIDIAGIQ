/**
 * Resolução da URL base da FastAPI para Route Handlers (proxy e BFF auth).
 *
 * Camada: utilitário servidor Next.js (Node). Não importar em Client Components.
 */

import fs from "node:fs";

export function isLikelyDockerContainer(): boolean {
  try {
    return fs.existsSync("/.dockerenv");
  } catch {
    return false;
  }
}

/** Mesma regra que `app/api-backend/[[...slug]]/route.ts` antes da extracção. */
export function resolveApiUpstreamBase(): string | null {
  const explicit = process.env.API_PROXY_TARGET?.trim();
  if (explicit) return explicit.replace(/\/$/, "");
  if (process.env.NODE_ENV === "production") return null;
  if (isLikelyDockerContainer()) return "http://api:8000";
  return "http://127.0.0.1:60000";
}
