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

export type RefazerQuestionarioResponse = {
  diagnostico_id: string;
  retificacao_id: string;
  score_geral: number;
  refazer_lote: number;
};

/** Recalcula score e grava retificação no mesmo `diagnostico_id` (plano avançado). */
export async function postRefazerQuestionarioCiclo(
  diagnosticoId: string,
  payload: DiagnosticoPayloadArmazenado,
): Promise<RefazerQuestionarioResponse> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Entre na plataforma antes de refazer o questionário.");
  }

  const idempotencyKey = obterIdempotencyKeyPostDiagnostico();
  const base = getApiUrlForFetch().replace(/\/$/, "");

  try {
    const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/refazer-questionario`, {
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
      const parsed = JSON.parse(raw) as RefazerQuestionarioResponse;
      limparIdempotencyKeyPostDiagnostico();
      return parsed;
    } catch {
      throw new Error(mensagemErroPostDiagnostico(res.status, raw));
    }
  } catch (error) {
    if (isLikelyNetworkFetchFailure(error)) {
      const tecnico = error instanceof Error ? error.message : String(error);
      throw new Error(`${mensagemConectividadeApiParaUsuario(base)} Detalhe: ${tecnico}`);
    }
    throw error;
  }
}

export type QuestionarioRespostaItemApi = {
  pergunta_id: string;
  pergunta_codigo: string;
  valor_bruto: unknown;
};

export type QuestionarioRespostasApi = {
  diagnostico_id: string;
  total: number;
  respostas: QuestionarioRespostaItemApi[];
};

/** Carrega respostas materializadas do ciclo para pré-preencher o assistente. */
export async function fetchQuestionarioRespostasPainel(
  diagnosticoId: string,
): Promise<QuestionarioRespostasApi> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão na plataforma necessária.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/questionario-respostas`, {
    headers: cabecalhosAuthPainelOpcional(),
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) {
      throw new Error("Sessão expirada — a abrir o login.");
    }
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  return JSON.parse(raw) as QuestionarioRespostasApi;
}
