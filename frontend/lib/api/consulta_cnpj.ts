/**
 * POST `/referencia/cnpj/consulta_cnpj` — Bearer painel (`admin_token`).
 *
 * Fluxo público OTP não expõe este endpoint; pré-preenchimento só com sessão na plataforma.
 */

import type { CnpjCanonicoCampos } from "@/lib/cnpj/canonical_merge";

import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

export type ConsultarCnpjResponseApi = {
  consulta_id: string;
  cnpj: string;
  fonte: string;
  canonico: CnpjCanonicoCampos & { cnpj: string };
  expira_cadastral_em: string;
  expira_qualificacao_em: string;
  expira_situacao_em: string;
  aplicado_em_diagnostico_em_andamento?: boolean;
};

function novoIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function mensagemErroHttp(res: Response): Promise<string> {
  const errorData: unknown = await res.json().catch(() => ({}));
  if (!errorData || typeof errorData !== "object") {
    return `Não foi possível consultar o CNPJ agora (HTTP ${res.status}).`;
  }
  const detail = (errorData as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { msg?: string }) => (typeof d?.msg === "string" ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (detail !== undefined) return JSON.stringify(detail);
  return `Não foi possível consultar o CNPJ agora (HTTP ${res.status}).`;
}

/** Rótulos amigáveis para `ConsultarCnpjResponse.fonte`. */
export function rotuloFonteConsultaCnpj(fonte: string): string {
  const f = fonte.trim().toLowerCase();
  if (f === "brasil_api" || f === "brasilapi") return "BrasilAPI";
  if (f.includes("minha_receita") || f === "minha_receita") return "Minha Receita";
  return fonte;
}

/** Consulta dados públicos e materializa snapshot (cache TTL por volatilidade). */
export async function postConsultarCnpjAutenticado(params: {
  cnpj14: string;
  forceRefresh?: boolean;
  aplicarNoDiagnosticoId?: string | null;
}): Promise<ConsultarCnpjResponseApi> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Entre na plataforma para buscar dados públicos pelo CNPJ.");
  }

  const base = getApiUrlForFetch().replace(/\/$/, "");
  const body: Record<string, unknown> = {
    cnpj: params.cnpj14.replace(/\D/g, ""),
    force_refresh: Boolean(params.forceRefresh),
  };
  if (params.aplicarNoDiagnosticoId?.trim()) {
    body.aplicar_no_diagnostico_id = params.aplicarNoDiagnosticoId.trim();
  }

  try {
    const res = await fetch(`${base}/referencia/cnpj/consulta_cnpj`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...cabecalhosAuthPainelOpcional(),
        "Idempotency-Key": novoIdempotencyKey(),
      },
      credentials: "include",
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      throw new Error(await mensagemErroHttp(res));
    }

    return (await res.json()) as ConsultarCnpjResponseApi;
  } catch (error) {
    if (isLikelyNetworkFetchFailure(error)) {
      const tecnico = error instanceof Error ? error.message : String(error);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw error;
  }
}
