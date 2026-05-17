import type { DiagnosticoPayloadArmazenado } from "../schemas/wizard";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";

import { cabecalhosAuthPainelOpcional, getApiUrlForFetch, temSessaoPainelParaApiCliente } from "./config";
import {
  isLikelyNetworkFetchFailure,
  mensagemConectividadeApiParaUsuario,
  mensagemErroHttp,
  mensagemErroPostDiagnostico,
} from "./http_errors";
import {
  limparIdempotencyKeyPostDiagnostico,
  obterIdempotencyKeyPostDiagnostico,
} from "@/lib/wizard/post_diagnostico_idempotency";

/**
 * Cria diagnóstico na API FastAPI — persistência em PostgreSQL (Supabase), isolada por `tenant_id` do JWT (RLS).
 * Exige Bearer JWT (`/login`) + header Idempotency-Key (contrato API).
 * Envia `aceite_termos_privacidade` para LGPD (migração 0012).
 */
export async function postDiagnostico(payload: DiagnosticoPayloadArmazenado) {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error(
      "Entre na plataforma antes de enviar o diagnóstico para o painel."
    );
  }

  const idempotencyKey = obterIdempotencyKeyPostDiagnostico();

  const base = getApiUrlForFetch().replace(/\/$/, "");

  try {
    const res = await fetch(`${base}/diagnosticos`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...cabecalhosAuthPainelOpcional(),
        "Idempotency-Key": idempotencyKey,
      },
      credentials: "include",
      body: JSON.stringify(payload),
    });

    const raw = await res.text();
    if (!res.ok) {
      if (encerrarSessaoPainelSe401(res.status)) {
        throw new Error("Sessão expirada — a abrir o login.");
      }
      throw new Error(mensagemErroPostDiagnostico(res.status, raw));
    }
    try {
      const parsed = JSON.parse(raw) as unknown;
      limparIdempotencyKeyPostDiagnostico();
      return parsed;
    } catch {
      throw new Error(mensagemErroPostDiagnostico(res.status, raw));
    }
  } catch (error) {
    console.error("Falha ao enviar diagnóstico:", error);
    if (isLikelyNetworkFetchFailure(error)) {
      const tecnico = error instanceof Error ? error.message : String(error);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw error;
  }
}
