import { getAccessToken, getApiUrlForFetch } from "./config";

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
  const url = new URL(`${base}/diagnosticos/`);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));

  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = (err as { detail?: string }).detail ?? res.statusText;
    throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
  }
  return res.json() as Promise<DiagnosticoResumoApi[]>;
}
