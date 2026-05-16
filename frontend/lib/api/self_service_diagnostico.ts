/**
 * Fluxo lead sem conta na plataforma: OTP no e-mail → JWT curto → POST /diagnosticos/self-service.
 *
 * Ordem: solicitar código → trocar por token (consome OTP) → gravar payload (Idempotency-Key).
 */

import type { DiagnosticoPayloadArmazenado } from "@/lib/schemas/wizard";
import type { SelfServiceDiagnosticoResultado } from "@/lib/wizard/self_service_result";

import { getApiUrlForFetch } from "./config";

function apiBase(): string {
  return getApiUrlForFetch().replace(/\/$/, "");
}

function novoIdempotencyKey(): string {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

async function mensagemErroHttp(res: Response): Promise<string> {
  const errorData: unknown = await res.json().catch(() => ({}));
  if (!errorData || typeof errorData !== "object") {
    return `Não foi possível concluir a solicitação agora (HTTP ${res.status}).`;
  }
  const detail = (errorData as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d: { msg?: string }) => (typeof d?.msg === "string" ? d.msg : JSON.stringify(d)))
      .join("; ");
  }
  if (detail !== undefined) return JSON.stringify(detail);
  return `Não foi possível concluir a solicitação agora (HTTP ${res.status}).`;
}

/** Dispara envio do código numérico por e-mail (Mailpit em dev). */
export async function postSolicitarCodigoEmail(email: string): Promise<{ mensagem: string }> {
  const res = await fetch(`${apiBase()}/auth/verificar-email/solicitar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return (await res.json()) as { mensagem: string };
}

/** Consome o OTP e devolve Bearer JWT para POST /diagnosticos/self-service. */
export async function postSelfServiceToken(
  email: string,
  codigo: string,
): Promise<{ access_token: string; expires_in: number }> {
  const res = await fetch(`${apiBase()}/auth/self-service/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, codigo: codigo.trim() }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return (await res.json()) as { access_token: string; expires_in: number };
}

/** Grava rascunho na BD (tenant self-service) e envia OTP — devolve token de resgate (fragmento de URL). */
export async function postRascunhoDiagnosticoSelfService(
  payload: DiagnosticoPayloadArmazenado,
): Promise<{ resgate_token: string; mensagem: string; expira_em: string }> {
  const res = await fetch(`${apiBase()}/diagnosticos/rascunho-self-service`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": novoIdempotencyKey(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return (await res.json()) as { resgate_token: string; mensagem: string; expira_em: string };
}

/** Metadados do rascunho para a página de OTP (sem JSON completo). */
export async function getRascunhoDiagnosticoSelfServiceResumo(resgateToken: string): Promise<{
  empresa_razao_social: string;
  /** CNPJ só com dígitos ou string vazia — se vazio, vincular à conta após login exige revisar o assistente (ADR-013). */
  empresa_cnpj: string;
  email_mascarado: string;
  respondente_email: string;
  expira_em: string;
}> {
  const res = await fetch(`${apiBase()}/diagnosticos/rascunho-self-service/resumo`, {
    method: "GET",
    headers: { "X-Rascunho-Token": resgateToken.trim() },
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  const j = (await res.json()) as {
    empresa_razao_social: string;
    empresa_cnpj?: string;
    email_mascarado: string;
    respondente_email: string;
    expira_em: string;
  };
  return {
    ...j,
    empresa_cnpj: typeof j.empresa_cnpj === "string" ? j.empresa_cnpj : "",
  };
}

/** GET público: lê snapshot do diagnóstico na BD com token emitido em concluir. */
export async function getConclusaoSelfServiceVisualizacao(
  diagnosticoId: string,
  leituraToken: string,
): Promise<SelfServiceDiagnosticoResultado> {
  const qs = new URLSearchParams({
    diagnostico_id: diagnosticoId.trim(),
    leitura_token: leituraToken.trim(),
  }).toString();
  // Não usar `new URL(string)` com base relativa (`/api-backend`) — falha no browser (Invalid URL).
  const res = await fetch(
    `${apiBase()}/diagnosticos/self-service/conclusao-visualizacao?${qs}`,
    { method: "GET" },
  );
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  const j: unknown = await res.json();
  if (!j || typeof j !== "object") {
    throw new Error("Não foi possível carregar o resultado agora. Tente novamente em instantes.");
  }
  const o = j as Record<string, unknown>;
  const id = o["id"] != null ? String(o["id"]) : "";
  const status = typeof o["status"] === "string" ? o["status"] : "";
  const empresa = typeof o["empresa_razao_social"] === "string" ? o["empresa_razao_social"] : "";
  const locale = typeof o["locale_relatorio"] === "string" ? o["locale_relatorio"] : "pt-BR";
  const sg = o["score_geral"];
  const score_geral =
    typeof sg === "number" && Number.isFinite(sg)
      ? sg
      : typeof sg === "string"
        ? (() => {
            const n = Number(sg.trim());
            return Number.isFinite(n) ? n : null;
          })()
        : null;
  const rawDims = o["scores_por_dimensao"];
  const scores_por_dimensao: SelfServiceDiagnosticoResultado["scores_por_dimensao"] = [];
  if (Array.isArray(rawDims)) {
    for (const row of rawDims) {
      if (!row || typeof row !== "object") continue;
      const r = row as Record<string, unknown>;
      const dimensao = typeof r["dimensao"] === "string" ? r["dimensao"] : "";
      const val = r["valor"];
      const valor =
        typeof val === "number" && Number.isFinite(val)
          ? val
          : typeof val === "string"
            ? (() => {
                const n = Number(String(val).trim());
                return Number.isFinite(n) ? n : null;
              })()
            : null;
      if (!dimensao || valor === null) continue;
      const pesoRaw = r["peso_total_aplicado"];
      let peso_total_aplicado: number | null = null;
      if (typeof pesoRaw === "number" && Number.isFinite(pesoRaw)) peso_total_aplicado = pesoRaw;
      else if (typeof pesoRaw === "string") {
        const p = Number(pesoRaw.trim());
        if (Number.isFinite(p)) peso_total_aplicado = p;
      }
      scores_por_dimensao.push({ dimensao, valor, peso_total_aplicado });
    }
  }
  const explRaw = o["explicacao_score_llm_texto"];
  const explicacao_score_llm_texto =
    typeof explRaw === "string" && explRaw.trim() ? explRaw.trim() : null;

  if (!id || !status || !empresa) {
    throw new Error("Não foi possível carregar o resultado agora. Tente novamente em instantes.");
  }
  return {
    id,
    status,
    empresa_razao_social: empresa,
    score_geral,
    scores_por_dimensao,
    locale_relatorio: locale || "pt-BR",
    explicacao_score_llm_texto,
  };
}

/** OTP + token de resgate → diagnóstico final (equivalente a self-service + JWT). */
export async function postConcluirRascunhoDiagnosticoSelfService(
  resgateToken: string,
  codigo: string,
): Promise<unknown> {
  const res = await fetch(`${apiBase()}/diagnosticos/rascunho-self-service/concluir`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": novoIdempotencyKey(),
    },
    body: JSON.stringify({ resgate_token: resgateToken.trim(), codigo: codigo.trim() }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return res.json();
}

/** JWT da conta na plataforma (opcional se cookie httpOnly) + token de resgate → diagnóstico no tenant. */
export async function postVincularRascunhoContaPlataforma(
  resgateToken: string,
  accessToken: string | null,
): Promise<unknown> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Idempotency-Key": novoIdempotencyKey(),
  };
  const t = accessToken?.trim();
  if (t) {
    headers.Authorization = `Bearer ${t}`;
  }
  const res = await fetch(`${apiBase()}/diagnosticos/rascunho-self-service/vincular-conta`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify({ resgate_token: resgateToken.trim() }),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return res.json();
}

/** Persiste diagnóstico no tenant self-service (JWT após OTP). */
export async function postDiagnosticoSelfService(
  payload: DiagnosticoPayloadArmazenado,
  accessToken: string,
): Promise<unknown> {
  const res = await fetch(`${apiBase()}/diagnosticos/self-service`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "Idempotency-Key": novoIdempotencyKey(),
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await mensagemErroHttp(res));
  }
  return res.json();
}
