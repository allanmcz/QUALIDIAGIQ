import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
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
/** Alinhado ao `Query(ge=1, le=200)` da API — página máxima por pedido. */
export const DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX = 200;

/**
 * Carrega **todas** as páginas de `GET /diagnosticos/?empresa_cnpj=` (ordenadas no servidor).
 * Usado na grelha por empresa quando o histórico pode exceder uma única página.
 *
 * Limite de segurança: no máximo 50 × 200 = 10 000 linhas; acima disso lança erro legível.
 */
export async function fetchDiagnosticosResumoTodasPaginasPorEmpresa(
  cnpj14: string,
): Promise<DiagnosticoResumoApi[]> {
  const PAGE = DIAGNOSTICOS_RESUMO_PAGE_SIZE_MAX;
  const MAX_PAGES = 50;
  const acc: DiagnosticoResumoApi[] = [];
  for (let p = 0; p < MAX_PAGES; p++) {
    const batch = await fetchDiagnosticosResumo(PAGE, p * PAGE, {
      empresaCnpj14: cnpj14,
    });
    acc.push(...batch);
    if (batch.length < PAGE) {
      return acc;
    }
  }
  throw new Error(
    `Esta empresa ultrapassa ${MAX_PAGES * PAGE} diagnósticos neste tenant no painel. Contacte suporte para relatório completo.`,
  );
}

export async function fetchDiagnosticosResumo(
  limit = 100,
  offset = 0,
  opts?: FetchDiagnosticosResumoOpts,
): Promise<DiagnosticoResumoApi[]> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  /** Não usar `new URL(relativo)` — com base `/api-backend` o browser lança «Invalid URL». */
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const cnpj = opts?.empresaCnpj14?.replace(/\D/g, "").trim();
  if (cnpj && cnpj.length === 14) {
    params.set("empresa_cnpj", cnpj);
  }
  const qs = params.toString();
  /** Sem barra final no path do browser — Next faz 308; o proxy normaliza para `/diagnosticos/` no upstream. */
  const url = `${base}/diagnosticos?${qs}`;

  try {
    const res = await fetch(url, {
      headers: { ...cabecalhosAuthPainelOpcional() },
      cache: "no-store",
      credentials: "include",
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
