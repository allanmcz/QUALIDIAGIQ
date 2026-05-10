/**
 * API LGPD — solicitações do titular e execução de anonimização (painel).
 *
 * Rotas: GET/PATCH/POST `/privacidade/...` com Bearer da conta na plataforma.
 */

import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { getAccessToken, getApiUrlForFetch } from "./config";
import { isLikelyNetworkFetchFailure, mensagemConectividadeApiParaUsuario } from "./http_errors";

/** Linha de `lgpd_titular_solicitacao` exposta pela API. */
export type SolicitacaoTitularLgpd = {
  id: string;
  tenant_id: string;
  diagnostico_id: string | null;
  tipo: string;
  status: string;
  canal: string;
  solicitante_email: string;
  payload: Record<string, unknown>;
  observacao_interna: string | null;
  actor_user_id: string | null;
  criado_em: string;
  atualizado_em: string;
};

/** Resposta de POST anonimizar-respondente. */
export type AnonimizarRespondenteLgpdResponse = {
  diagnostico_id: string;
  solicitacao_id: string;
  status_solicitacao?: string;
  mensagem?: string;
};

function baseUrl(): string {
  return getApiUrlForFetch().replace(/\/$/, "");
}

/**
 * Lista solicitações LGPD do tenant (JWT).
 *
 * @param params.status — filtro opcional (ex.: `deferida`).
 */
export async function fetchSolicitacoesLgpd(params?: {
  status?: string;
  limit?: number;
}): Promise<SolicitacaoTitularLgpd[]> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const sp = new URLSearchParams();
  if (params?.status) sp.set("status", params.status);
  if (params?.limit != null) sp.set("limit", String(params.limit));
  const qs = sp.toString();
  const url = `${baseUrl()}/privacidade/solicitacoes${qs ? `?${qs}` : ""}`;

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
    return res.json() as Promise<SolicitacaoTitularLgpd[]>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(baseUrl())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}

/** Atualiza status operacional da solicitação (triagem / deferimento). */
export async function patchStatusSolicitacaoLgpd(
  solicitacaoId: string,
  body: { status: string; observacao_interna?: string | null },
): Promise<SolicitacaoTitularLgpd> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const url = `${baseUrl()}/privacidade/solicitacoes/${solicitacaoId}/status`;
  try {
    const res = await fetch(url, {
      method: "PATCH",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<SolicitacaoTitularLgpd>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(baseUrl())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}

/**
 * Executa anonimização técnica do respondente (após solicitação tipo anonimização estar deferida).
 *
 * Requer diagnóstico `finalizado` no servidor (WORM + trigger).
 */
export async function postAnonimizarRespondenteLgpd(
  diagnosticoId: string,
  solicitacaoId: string,
): Promise<AnonimizarRespondenteLgpdResponse> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const url = `${baseUrl()}/privacidade/diagnosticos/${diagnosticoId}/anonimizar-respondente`;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ solicitacao_id: solicitacaoId }),
    });
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      const err = await res.json().catch(() => ({}));
      const detail = (err as { detail?: string }).detail ?? res.statusText;
      throw new Error(typeof detail === "string" ? detail : `Erro ${res.status}`);
    }
    return res.json() as Promise<AnonimizarRespondenteLgpdResponse>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(baseUrl())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}

/** Registra nova solicitação (demo / backoffice). Exige Idempotency-Key distinta por pedido. */
export async function postRegistrarSolicitacaoLgpd(body: {
  tipo: string;
  canal?: string;
  solicitante_email: string;
  diagnostico_id?: string | null;
  payload?: Record<string, unknown>;
}): Promise<SolicitacaoTitularLgpd> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const url = `${baseUrl()}/privacidade/solicitacoes`;
  const idempotencyKey =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({
        tipo: body.tipo,
        canal: body.canal ?? "plataforma",
        solicitante_email: body.solicitante_email,
        diagnostico_id: body.diagnostico_id ?? null,
        payload: body.payload ?? {},
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
    return res.json() as Promise<SolicitacaoTitularLgpd>;
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(baseUrl())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}

/** Formato do pacote ADR-012 §4 — alinhado a `FormatoExportPortabilidade` na API. */
export type FormatoExportPortabilidade = "json" | "pacote_pdf";

/**
 * Descarrega pacote de portabilidade (LGPD art. 18, V) após solicitação tipo **portabilidade** **deferida**.
 * GET — não usa Idempotency-Key. Devolve `Blob` (JSON ou PDF conforme `formato`).
 */
export async function fetchExportPortabilidadeDiagnostico(params: {
  diagnosticoId: string;
  solicitacaoId: string;
  formato?: FormatoExportPortabilidade;
}): Promise<Blob> {
  const token = getAccessToken();
  if (!token) {
    throw new Error("Sessão necessária.");
  }
  const sp = new URLSearchParams();
  sp.set("solicitacao_id", params.solicitacaoId);
  sp.set("formato", params.formato ?? "json");
  const url = `${baseUrl()}/privacidade/diagnosticos/${params.diagnosticoId}/export-portabilidade?${sp.toString()}`;

  try {
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
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
    return res.blob();
  } catch (e) {
    if (isLikelyNetworkFetchFailure(e)) {
      const tecnico = e instanceof Error ? e.message : String(e);
      throw new Error(`${mensagemConectividadeApiParaUsuario(baseUrl())} Detalhe: ${tecnico}`);
    }
    throw e;
  }
}
