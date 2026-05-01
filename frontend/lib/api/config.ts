/**
 * URL base da API QualiDiagIQ.
 * Docker Compose do repo expõe a API em localhost:60000 (host) -> 8000 (container).
 */
export function getApiUrl(): string {
  return (
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "http://localhost:60000"
  );
}

const TOKEN_KEY = "admin_token";

/** JWT salvo pelo fluxo de login MVP (`/login`). */
export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
