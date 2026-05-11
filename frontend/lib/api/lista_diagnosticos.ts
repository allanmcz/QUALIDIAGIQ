import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { getAccessToken, getApiUrlForFetch } from "./config";
import {
  isLikelyNetworkFetchFailure,
  mensagemConectividadeApiParaUsuario,
  mensagemErroHttp,
} from "./http_errors";

/** Resposta de GET /diagnosticos/ (lista resumida por tenant). */
export type DiagnosticoResumoApi = {
  id: string;
  empresa_razao_social: string;
  /** CNPJ 14 dígitos ou "" — agrupa ciclos «antes/depois» no mesmo tenant. */
  empresa_cnpj?: string;
  status: string;
  plano: string;
  score_geral: number | null;
  criado_em: string;
  finalizado_em: string | null;
  relatorio_pdf_url: string | null;
};

export type FetchDiagnosticosResumoOpts = {
  /** Filtra pela coluna `empresa_cnpj` (14 dígitos); omitir = todos do tenant. */
  empresaCnpj14?: string;
};

/**
 * Lista diagnósticos do tenant logado (JWT obrigatório).
 * P7 — lista de diagnósticos no painel (conta na plataforma).
 */
export async function fetchDiagnosticosResumo(
  limit = 100,
  offset = 0,
  opts?: FetchDiagnosticosResumoOpts,
): Promise<DiagnosticoResumoApi[]> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  /** Não usar `new URL(relativo)` — com base `/api-backend` o browser lança «Invalid URL». */
  const path = `${base}/diagnosticos/`;
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const cnpj = opts?.empresaCnpj14?.replace(/\D/g, "").trim();
  if (cnpj && cnpj.length === 14) {
    params.set("empresa_cnpj", cnpj);
  }
  const qs = params.toString();
  const url = `${path}?${qs}`;

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    const raw = await res.text();
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      /** Evita mostrar só «Internal Server Error» (statusText) quando o corpo é HTML/texto do Next/uvicorn. */
      throw new Error(mensagemErroHttp(res.status, raw));
    }
    try {
      return JSON.parse(raw) as DiagnosticoResumoApi[];
    } catch {
      throw new Error(mensagemErroHttp(res.status, raw));
    }
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
      const pedido =
        typeof window !== "undefined"
          ? `${window.location.origin}${url.startsWith("/") ? url : `/${url}`}`
          : url;
      throw new Error(
        `${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}. Pedido: ${pedido}`,
      );
    }
    throw e;
  }
}
