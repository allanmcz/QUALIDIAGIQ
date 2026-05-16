/**
 * DELETE /diagnosticos/empresa/{cnpj14} — exclusão em lote no painel (pré-WORM).
 */

import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
import {
  isLikelyNetworkFetchFailure,
  mensagemConectividadeApiParaUsuario,
  mensagemErroHttp,
} from "./http_errors";

export type EliminarEmpresaDiagnosticoResponse = {
  empresa_cnpj: string;
  total_eliminados: number;
  mantidos_finalizados: number;
  mantidos_outros_status: number;
  eliminados_ids: string[];
  mensagem: string;
};

function novoIdempotencyKey(): string {
  return crypto.randomUUID();
}

/**
 * Remove diagnósticos não finalizados do CNPJ no tenant do JWT.
 */
export async function deleteDiagnosticosEmpresaPainel(
  cnpj14: string,
): Promise<EliminarEmpresaDiagnosticoResponse> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const digits = cnpj14.replace(/\D/g, "");
  if (digits.length !== 14) {
    throw new Error("CNPJ inválido para exclusão (14 dígitos).");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const url = `${base}/diagnosticos/empresa/${digits}`;

  try {
    const res = await fetch(url, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        "Idempotency-Key": novoIdempotencyKey(),
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
    return JSON.parse(raw) as EliminarEmpresaDiagnosticoResponse;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}
