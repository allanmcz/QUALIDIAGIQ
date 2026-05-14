/**
 * POST /diagnosticos/vincular-leads-self-service — traz diagnósticos OTP (mesmo e-mail) para o tenant da conta na plataforma.
 */
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

export type VincularLeadsSelfServiceResult = {
  total_vinculados: number;
  diagnostico_ids: string[];
};

export async function postVincularLeadsSelfService(): Promise<VincularLeadsSelfServiceResult> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const idempotencyKey =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const base = getApiUrlForFetch().replace(/\/$/, "");
  try {
    const res = await fetch(`${base}/diagnosticos/vincular-leads-self-service`, {
      method: "POST",
      headers: {
        ...cabecalhosAuthPainelOpcional(),
        "Idempotency-Key": idempotencyKey,
      },
      credentials: "include",
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const raw = await res.text();
      let detail = raw;
      try {
        const j = JSON.parse(raw) as { detail?: unknown };
        if (typeof j.detail === "string") detail = j.detail;
        else if (j.detail != null) detail = JSON.stringify(j.detail);
      } catch {
        /* manter raw */
      }
      throw new Error(detail || `Erro ${res.status}`);
    }
    return (await res.json()) as VincularLeadsSelfServiceResult;
  } catch (error) {
    if (isLikelyNetworkFetchFailure(error)) {
      const tecnico = error instanceof Error ? error.message : String(error);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw error;
  }
}
