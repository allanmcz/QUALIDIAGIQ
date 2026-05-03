import { getAccessToken, getApiUrlForFetch } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

/** Resposta de GET /diagnosticos/ (lista resumida por tenant). */
export type DiagnosticoResumoApi = {
  id: string;
  empresa_razao_social: string;
  status: string;
  plano: string;
  score_geral: number | null;
  criado_em: string;
  finalizado_em: string | null;
  relatorio_pdf_url: string | null;
};

/**
 * Lista diagnósticos do tenant logado (JWT obrigatório).
 * P7 — dashboard B2B.
 */
export async function fetchDiagnosticosResumo(
  limit = 100,
  offset = 0,
): Promise<DiagnosticoResumoApi[]> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  /** Não usar `new URL(relativo)` — com base `/api-backend` o browser lança «Invalid URL». */
  const path = `${base}/diagnosticos/`;
  const qs = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  }).toString();
  const url = `${path}?${qs}`;

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<DiagnosticoResumoApi[]>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}
