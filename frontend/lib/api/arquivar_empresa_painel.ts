import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  temSessaoPainelParaApiCliente,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import { mensagemErroHttp } from "@/lib/api/http_errors";

export type ArquivarEmpresaPainelResponse = {
  empresa_cnpj: string;
  arquivado: boolean;
  estado_alterado: boolean;
  mensagem: string;
};

export type EmpresaArquivoStatusResponse = {
  empresa_cnpj: string;
  arquivado: boolean;
};

export async function fetchEmpresaArquivoStatus(cnpj14: string): Promise<EmpresaArquivoStatusResponse> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/empresa/${cnpj14}/arquivo`, {
    headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  return JSON.parse(raw) as EmpresaArquivoStatusResponse;
}

export async function patchArquivarEmpresaPainel(
  cnpj14: string,
  arquivado: boolean,
): Promise<ArquivarEmpresaPainelResponse> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/empresa/${cnpj14}/arquivo`, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...cabecalhosAuthPainelOpcional(),
    },
    body: JSON.stringify({ arquivado }),
    cache: "no-store",
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  return JSON.parse(raw) as ArquivarEmpresaPainelResponse;
}

/** Lista CNPJs arquivados do tenant (painel). */
export async function fetchCnpjsArquivadosPainel(): Promise<string[]> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/cnpjs-arquivados`, {
    headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  const data = JSON.parse(raw) as { cnpjs?: string[] };
  return Array.isArray(data.cnpjs) ? data.cnpjs : [];
}

/** Atalho POST desarquivar — restaura empresa na listagem principal. */
export async function desarquivarEmpresaPainel(cnpj14: string): Promise<ArquivarEmpresaPainelResponse> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/empresa/${cnpj14}/desarquivar`, {
    method: "POST",
    headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  return JSON.parse(raw) as ArquivarEmpresaPainelResponse;
}
