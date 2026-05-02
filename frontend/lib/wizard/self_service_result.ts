/**
 * Resultado do POST self-service — guardado em sessionStorage até à página de conclusão.
 */

import { ORDEM_DIMENSOES_API } from "@/lib/wizard/dimensao_labels";

/** Snapshot atual (inclui `score_api` para hidratar dimensões). Leitura aceita ainda a chave v1 legada. */
export const STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT = "qdi_self_service_diag_result_v2";
const STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT_LEGACY = "qdi_self_service_diag_result_v1";

/** Uma linha do breakdown por dimensão (transparência M03 — mesmo critério do relatório). */
export type ScorePorDimensaoItem = {
  dimensao: string;
  valor: number;
  peso_total_aplicado: number | null;
};

export type SelfServiceDiagnosticoResultado = {
  id: string;
  status: string;
  empresa_razao_social: string;
  score_geral: number | null;
  /** Opcional — versões antigas do snapshot só tinham score geral. */
  scores_por_dimensao: ScorePorDimensaoItem[];
  locale_relatorio: string;
};

/** Payload ao gravar — inclui cópia bruta de `score` da API para hidratar dimensões em leituras antigas. */
export type SelfServiceDiagnosticoPersistPayload = SelfServiceDiagnosticoResultado & {
  score_api?: unknown;
};

/**
 * Converte `score.score_por_dimensao` do JSON da API (mapa slug → { valor, peso_total_aplicado }) em lista ordenada.
 */
export function scoresPorDimensaoFromApiScore(score: unknown): ScorePorDimensaoItem[] {
  if (!score || typeof score !== "object") return [];
  const spd = (score as Record<string, unknown>)["score_por_dimensao"];
  if (!spd || typeof spd !== "object" || Array.isArray(spd)) return [];
  const ordem = new Map<string, number>(ORDEM_DIMENSOES_API.map((d, i) => [d, i]));
  const items: ScorePorDimensaoItem[] = [];
  for (const [dimensao, raw] of Object.entries(spd)) {
    if (!raw || typeof raw !== "object") continue;
    const r = raw as Record<string, unknown>;
    const valorRaw = r["valor"];
    let valor: number | null = null;
    if (typeof valorRaw === "number" && Number.isFinite(valorRaw)) valor = valorRaw;
    else if (typeof valorRaw === "string") {
      const n = Number(valorRaw.trim());
      if (Number.isFinite(n)) valor = n;
    }
    if (valor === null) continue;
    const pesoRaw = r["peso_total_aplicado"];
    let peso_total_aplicado: number | null = null;
    if (typeof pesoRaw === "number" && Number.isFinite(pesoRaw)) peso_total_aplicado = pesoRaw;
    else if (typeof pesoRaw === "string") {
      const p = Number(pesoRaw.trim());
      if (Number.isFinite(p)) peso_total_aplicado = p;
    }
    items.push({ dimensao, valor, peso_total_aplicado });
  }
  items.sort((a, b) => (ordem.get(a.dimensao) ?? 99) - (ordem.get(b.dimensao) ?? 99));
  return items;
}

function scoresPorDimensaoFromArraySalva(scoresRaw: unknown): ScorePorDimensaoItem[] {
  const scores_por_dimensao: ScorePorDimensaoItem[] = [];
  if (!Array.isArray(scoresRaw)) return scores_por_dimensao;
  for (const row of scoresRaw) {
    if (!row || typeof row !== "object") continue;
    const r = row as Record<string, unknown>;
    const dim = r["dimensao"];
    const val = r["valor"];
    const peso = r["peso_total_aplicado"];
    if (typeof dim !== "string") continue;
    const valorNum = typeof val === "number" ? val : typeof val === "string" ? Number(val.trim()) : NaN;
    if (!Number.isFinite(valorNum)) continue;
    let pesoNum: number | null = null;
    if (typeof peso === "number" && Number.isFinite(peso)) pesoNum = peso;
    else if (typeof peso === "string") {
      const p = Number(peso.trim());
      if (Number.isFinite(p)) pesoNum = p;
    }
    scores_por_dimensao.push({ dimensao: dim, valor: valorNum, peso_total_aplicado: pesoNum });
  }
  return scores_por_dimensao;
}

export function saveSelfServiceDiagnosticoResultado(data: SelfServiceDiagnosticoPersistPayload): void {
  if (typeof window === "undefined") return;
  try {
    const payload = JSON.stringify(data);
    sessionStorage.setItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT, payload);
    sessionStorage.removeItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT_LEGACY);
  } catch {
    /* quota */
  }
}

export function loadSelfServiceDiagnosticoResultado(): SelfServiceDiagnosticoResultado | null {
  if (typeof window === "undefined") return null;
  try {
    const raw =
      sessionStorage.getItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT) ??
      sessionStorage.getItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT_LEGACY);
    if (!raw) return null;
    const data: unknown = JSON.parse(raw);
    if (!data || typeof data !== "object") return null;
    const o = data as Record<string, unknown>;
    const idRaw = o["id"];
    const id =
      typeof idRaw === "string"
        ? idRaw
        : typeof idRaw === "number" && Number.isFinite(idRaw)
          ? String(idRaw)
          : null;
    const status = o["status"];
    const empresa_razao_social = o["empresa_razao_social"];
    const locale_relatorio = o["locale_relatorio"];
    const score_geral = o["score_geral"];
    const scoresRaw = o["scores_por_dimensao"];
    const scoreApi = o["score_api"];
    if (id === null || typeof status !== "string") return null;
    if (typeof empresa_razao_social !== "string") return null;
    if (typeof locale_relatorio !== "string") return null;
    const score =
      score_geral === null || score_geral === undefined
        ? null
        : typeof score_geral === "number"
          ? score_geral
          : Number(score_geral);

    let scores_por_dimensao = scoresPorDimensaoFromArraySalva(scoresRaw);
    if (scores_por_dimensao.length === 0 && scoreApi !== undefined) {
      scores_por_dimensao = scoresPorDimensaoFromApiScore(scoreApi);
    }

    return {
      id,
      status,
      empresa_razao_social,
      locale_relatorio,
      score_geral: Number.isFinite(score) ? score : null,
      scores_por_dimensao,
    };
  } catch {
    return null;
  }
}

export function clearSelfServiceDiagnosticoResultado(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT);
    sessionStorage.removeItem(STORAGE_SELF_SERVICE_DIAGNOSTICO_RESULT_LEGACY);
  } catch {
    /* ignore */
  }
}
