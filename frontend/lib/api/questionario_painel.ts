import {
  cabecalhosAuthPainelOpcional,
  getApiUrlForFetch,
  temSessaoPainelParaApiCliente,
} from "@/lib/api/config";
import { encerrarSessaoPainelSe401 } from "@/lib/auth/painel_session";
import { mensagemErroHttp } from "@/lib/api/http_errors";

export const MAX_DIAGNOSTICOS_COMPARACAO = 5;
export const MIN_DIAGNOSTICOS_COMPARACAO = 2;

export type RespostaQuestionarioItemApi = {
  ordem_exibicao: number;
  pergunta_id: string;
  pergunta_codigo: string;
  dimensao: string;
  tipo_pergunta: string;
  texto_pergunta: string;
  peso: number;
  base_legal?: string | null;
  pilar_abnt?: string | null;
  valor_bruto: unknown;
  valor_exibicao: string;
  pontuacao_item: number | null;
  excluida_calculo: boolean;
  criado_em?: string | null;
};

export type ComparacaoQuestionarioApi = {
  empresa_cnpj: string;
  empresa_razao_social: string;
  diagnosticos: Array<{
    diagnostico_id: string;
    finalizado_em: string | null;
    score_geral: number | null;
    numero_interno_grupo: number | null;
    total_respostas: number;
  }>;
  linhas: Array<{
    pergunta_codigo: string;
    texto_pergunta: string;
    dimensao: string;
    base_legal?: string | null;
    valores_por_diagnostico: Record<
      string,
      {
        valor_exibicao: string;
        pontuacao_item: number | null;
        excluida_calculo: boolean;
        ordem_exibicao: number | null;
      }
    >;
  }>;
};

export async function fetchCompararQuestionario(
  diagnosticoIds: string[],
): Promise<ComparacaoQuestionarioApi> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const qs = new URLSearchParams({ ids: diagnosticoIds.join(",") });
  const res = await fetch(`${base}/diagnosticos/comparar-questionario?${qs}`, {
    headers: { Accept: "application/json", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  const raw = await res.text();
  if (!res.ok) {
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  return JSON.parse(raw) as ComparacaoQuestionarioApi;
}

/** Abre PDF do questionário em nova aba (Bearer via fetch). */
export async function abrirPdfQuestionarioDiagnostico(diagnosticoId: string): Promise<void> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const res = await fetch(`${base}/diagnosticos/${diagnosticoId}/questionario-respostas/pdf`, {
    headers: { Accept: "application/pdf", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  if (!res.ok) {
    const raw = await res.text();
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

/** Abre PDF da comparação entre ciclos selecionados. */
export async function abrirPdfComparacaoQuestionario(diagnosticoIds: string[]): Promise<void> {
  if (!temSessaoPainelParaApiCliente()) {
    throw new Error("Sessão necessária: faça login em /login.");
  }
  const base = getApiUrlForFetch().replace(/\/$/, "");
  const qs = new URLSearchParams({ ids: diagnosticoIds.join(",") });
  const res = await fetch(`${base}/diagnosticos/comparar-questionario/pdf?${qs}`, {
    headers: { Accept: "application/pdf", ...cabecalhosAuthPainelOpcional() },
    cache: "no-store",
    credentials: "include",
  });
  if (!res.ok) {
    const raw = await res.text();
    if (encerrarSessaoPainelSe401(res.status)) throw new Error("Sessão expirada.");
    throw new Error(mensagemErroHttp(res.status, raw));
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
