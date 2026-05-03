import type { DiagnosticoPayload } from "../schemas/wizard";
import { getAccessToken, getApiUrlForFetch } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

/**
 * Cria diagnóstico na API FastAPI — persistência em PostgreSQL (Supabase), isolada por `tenant_id` do JWT (RLS).
 * Exige Bearer JWT (`/login`) + header Idempotency-Key (contrato API).
 * Envia `aceite_termos_privacidade` para LGPD (migração 0012).
 */
export async function postDiagnostico(payload: DiagnosticoPayload) {
  const token = getAccessToken();
  if (!token) {
    throw new Error(
      "Sessão necessária: faça login em /login antes de enviar o diagnóstico (Bearer JWT)."
    );
  }

  const idempotencyKey =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  const base = getApiUrlForFetch().replace(/\/$/, "");

  try {
    const res = await fetch(`${base}/diagnosticos/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      const detail = errorData.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ")
            : detail
              ? JSON.stringify(detail)
              : `Erro na API: ${res.status}`;
      throw new Error(msg);
    }

    return await res.json();
  } catch (error) {
    console.error("Falha ao enviar diagnóstico:", error);
    if (isLikelyNetworkFetchFailure(error)) {
      const tecnico = error instanceof Error ? error.message : String(error);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw error;
  }
}
