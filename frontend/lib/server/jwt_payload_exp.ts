/**
 * Extracção mínima do claim `exp` de um JWT (sem verificação criptográfica).
 *
 * Usado só para `Max-Age` de cookie e checagem de expiração grosseira no BFF.
 */

export function jwtExpUnixSeconds(token: string): number | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const segment = parts[1] ?? "";
    const normalizado = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalizado.padEnd(Math.ceil(normalizado.length / 4) * 4, "=");
    const payload = JSON.parse(Buffer.from(padded, "base64").toString("utf8")) as { exp?: unknown };
    const exp = Number(payload.exp);
    if (!Number.isFinite(exp) || exp <= 0) return null;
    return exp;
  } catch {
    return null;
  }
}

/** Decodifica payload JWT (sem verificar assinatura) — apenas leitura de claims não sensíveis. */
export function jwtPayloadRecord(token: string): Record<string, unknown> | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const segment = parts[1] ?? "";
    const normalizado = segment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalizado.padEnd(Math.ceil(normalizado.length / 4) * 4, "=");
    const raw = JSON.parse(Buffer.from(padded, "base64").toString("utf8"));
    if (!raw || typeof raw !== "object") return null;
    return raw as Record<string, unknown>;
  } catch {
    return null;
  }
}
