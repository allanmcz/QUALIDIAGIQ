/**
 * POST `/diagnosticos/{id}/explicacao-score-llm` — narrativa LLM sobre o score (painel, ADR-022).
 *
 * Exige sessão na plataforma (Bearer) e header `Idempotency-Key` (middleware + replay 2xx).
 */

import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

/** Espelha `ExplicarScoreLlmHttpResponse` da API FastAPI. */
export type ExplicacaoScoreLlmHttp = {
  text: string;
  provider: string;
  model: string;
  policy_version: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  blocked_by_guardrail: boolean;
  guardrail_reason: string | null;
  guardrail_status: string;
};

function base(): string {
  return getApiUrlForFetch().replace(/\/$/, "");
}

export function novaIdempotencyKeyExplicacaoScore(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/**
 * Solicita explicação narrativa do score já calculado (não recalcula o motor 0–100).
 *
 * @param idempotencyKey — chave estável para replay; omitir gera UUID novo por pedido.
 */
export async function postExplicacaoScoreLlm(
  diagnosticoId: string,
  idempotencyKey?: string,
): Promise<ExplicacaoScoreLlmHttp> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária.");
  }
  const url = `${base()}/diagnosticos/${diagnosticoId}/explicacao-score-llm`;
  const key = (idempotencyKey ?? novaIdempotencyKeyExplicacaoScore()).trim();

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...cabecalhosAuthPainelOpcional(),
        "Idempotency-Key": key,
      },
      credentials: "include",
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<ExplicacaoScoreLlmHttp>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}
