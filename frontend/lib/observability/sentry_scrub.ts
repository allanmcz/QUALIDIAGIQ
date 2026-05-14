/**
 * Redação de PII antes do envio ao Sentry (browser).
 *
 * Alinhado a QDI-H-016 e ao hook ``before_send`` da API em ``src/presentation/api/main.py``.
 * Melhor esforço — não substitui DLP nem revisão de breadcrumbs personalizados.
 */

import type { ErrorEvent, EventHint } from "@sentry/core";

const CHAVES_SENSIVEIS = [
  "password",
  "senha",
  "codigo",
  "token",
  "authorization",
  "email",
  "e-mail",
  "telefone",
  "celular",
  "otp",
  "cpf",
] as const;

function chaveSensivel(nome: string): boolean {
  const lower = nome.toLowerCase();
  return CHAVES_SENSIVEIS.some((s) => lower.includes(s));
}

function redactRecord(obj: Record<string, unknown>): void {
  for (const k of Object.keys(obj)) {
    if (chaveSensivel(k)) {
      obj[k] = "[REDACTED]";
    }
  }
}

/**
 * ``beforeSend`` do SDK browser — devolve o evento (mutado) ou ``null`` para descartar.
 *
 * Assinatura alinhada a ``@sentry/browser`` / ``ClientOptions['beforeSend']`` (``ErrorEvent`` + ``EventHint``).
 */
export function sentryBrowserBeforeSend(event: ErrorEvent, hint: EventHint): ErrorEvent | null {
  void hint;
  try {
    const ev = event as unknown as Record<string, unknown>;
    const req = ev.request;
    if (req && typeof req === "object") {
      const r = req as Record<string, unknown>;
      const data = r.data;
      if (data && typeof data === "object" && !Array.isArray(data)) {
        redactRecord(data as Record<string, unknown>);
      }
    }
    const user = ev.user;
    if (user && typeof user === "object") {
      const u = user as Record<string, unknown>;
      for (const k of ["email", "username", "ip_address", "telefone", "celular", "phone"]) {
        if (k in u) {
          u[k] = "[REDACTED]";
        }
      }
    }
    const extra = ev.extra;
    if (extra && typeof extra === "object" && !Array.isArray(extra)) {
      redactRecord(extra as Record<string, unknown>);
    }
  } catch {
    // Nunca bloquear o pipeline de erro por falha de scrub.
  }
  return event;
}
