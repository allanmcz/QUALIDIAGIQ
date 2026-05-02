/**
 * Fluxo lead sem conta B2B: OTP no e-mail → JWT curto → POST /diagnosticos/self-service.
 *
 * Ordem: solicitar código → trocar por token (consome OTP) → gravar payload (Idempotency-Key).
 */

import type { DiagnosticoPayload } from "@/lib/schemas/wizard";

import { getApiUrlForFetch } from "./config";

function apiBase(): string {
  return getApiUrlForFetch().replace(/\/$/, "");
}

function novoIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function mensagemErroHttp(res: Response): Promise<string> {
  const errorData: unknown = await res.json().catch(() => ({}));
  if (!errorData || typeof errorData !== "object") {
    return `Erro na API: ${res.status}`;
  }
  const detail = (errorData as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { msg?: string }) => (typeof d?.msg === "string" ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (detail !== undefined) return JSON.stringify(detail);
  return `Erro na API: ${res.status}`;
}

/** Dispara envio do código numérico por e-mail (Mailpit em dev). */
export async function postSolicitarCodigoEmail(email: string): Promise<{ mensagem: string }> {
  const res = await fetch(`${apiBase()}/auth/verificar-email/solicitar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return (await res.json()) as { mensagem: string };
}

/** Consome o OTP e devolve Bearer JWT para POST /diagnosticos/self-service. */
export async function postSelfServiceToken(
  email: string,
  codigo: string,
): Promise<{ access_token: string; expires_in: number }> {
  const res = await fetch(`${apiBase()}/auth/self-service/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, codigo: codigo.trim() }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return (await res.json()) as { access_token: string; expires_in: number };
}

/** Persiste diagnóstico no tenant self-service (JWT após OTP). */
export async function postDiagnosticoSelfService(
  payload: DiagnosticoPayload,
  accessToken: string,
): Promise<unknown> {
  const res = await fetch(`${apiBase()}/diagnosticos/self-service`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "Idempotency-Key": novoIdempotencyKey(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return res.json();
}
