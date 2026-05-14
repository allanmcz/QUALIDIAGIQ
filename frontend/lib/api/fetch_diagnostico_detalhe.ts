import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  normalizarHrefRelatorioPdf,
  temSessaoPainelParaApiCliente,
} from "./config";
import {
  isLikelyNetworkFetchFailure,
  mensagemConectividadeApiParaUsuario,
  mensagemErroHttp,
} from "./http_errors";

/** GET /diagnosticos/{id} — Bearer obrigatório no painel. */
export async function fetchDiagnosticoDetalhe(diagnosticoId: string): Promise<DiagnosticoDetalheApi> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const url = `${base}/diagnosticos/${diagnosticoId}`;
  try {
    const res = await fetch(url, {
      headers: {
        Accept: "application/json",
        ...cabecalhosAuthPainelOpcional(),
      },
      cache: "no-store",
      credentials: "include",
    });
    const raw = await res.text();
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      throw new Error(mensagemErroHttp(res.status, raw));
    }
    try {
      return JSON.parse(raw) as DiagnosticoDetalheApi;
    } catch {
      throw new Error(mensagemErroHttp(res.status, raw));
    }
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? `${e.name}: ${e.message}` : String(e);
      throw new Error(
        `${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}. Pedido: ${url}`,
      );
    }
    throw e;
  }
}

/** URL segura para abrir PDF em nova aba (relativo → absoluto quando aplicável). */
export function hrefRelatorioPdfAbsoluto(urlRelatorio: string | null): string | null {
  if (!urlRelatorio?.trim()) return null;
  return normalizarHrefRelatorioPdf(urlRelatorio) ?? urlRelatorio;
}
