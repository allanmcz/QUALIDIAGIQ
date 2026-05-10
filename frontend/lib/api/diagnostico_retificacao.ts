/**
 * Retificações append-only do diagnóstico (ADR-012 §5 — cadeia de hashes; sem UPDATE no original).
 *
 * Rotas: GET/POST `/diagnosticos/{id}/retificacoes` e `/retificacao` com Bearer do painel.
 */

import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { getAccessToken, getApiUrlForFetch } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

/** Resposta de uma linha em `diagnostico_retificacao` (schema HTTP da API). */
export type DiagnosticoRetificacaoHttp = {
  id: string;
  tenant_id: string;
  diagnostico_original_id: string;
  hash_diagnostico_original_sha256: string;
  motivo_retificacao: string;
  payload_retificacao: Record<string, unknown>;
  hash_retificacao_sha256: string;
  actor_user_id: string | null;
  criado_em: string;
};

function base(): string {
  return getApiUrlForFetch().replace(/\/$/, "");
}

function novaIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

/** Lista retificações do diagnóstico (mais recentes primeiro). */
export async function fetchRetificacoesDiagnostico(
  diagnosticoId: string,
  params?: { limit?: number },
): Promise<DiagnosticoRetificacaoHttp[]> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const sp = new URLSearchParams();
  if (params?.limit != null) sp.set("limit", String(params.limit));
  const qs = sp.toString();
  const url = `${base()}/diagnosticos/${diagnosticoId}/retificacoes${qs ? `?${qs}` : ""}`;

  try {
    const res = await fetch(url, {
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<DiagnosticoRetificacaoHttp[]>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}

/** Regista nova retificação na cadeia (POST — exige `Idempotency-Key` no servidor). */
export async function postRetificacaoDiagnostico(
  diagnosticoId: string,
  body: { motivo_retificacao: string; payload_retificacao?: Record<string, unknown> },
): Promise<DiagnosticoRetificacaoHttp> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const url = `${base()}/diagnosticos/${diagnosticoId}/retificacao`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": novaIdempotencyKey(),
      },
      body: JSON.stringify({
        motivo_retificacao: body.motivo_retificacao,
        payload_retificacao: body.payload_retificacao ?? {},
      }),
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<DiagnosticoRetificacaoHttp>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}
