import type { DiagnosticoPayload } from "../schemas/wizard";
import { getAccessToken, getApiUrl } from "./config";

type PayloadApi = Omit<DiagnosticoPayload, "aceite_termos_privacidade">;

function stripLeadFields(payload: DiagnosticoPayload): PayloadApi {
  const { aceite_termos_privacidade: _aceite, ...rest } = payload;
  void _aceite;
  return rest;
}

/**
 * Cria diagnóstico. Exige JWT (login `/login`) + header Idempotency-Key (contrato API).
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

  const base = getApiUrl().replace(/\/$/, "");
  const body = stripLeadFields(payload);

  try {
    const res = await fetch(`${base}/diagnosticos/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(body),
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
    throw error;
  }
}
