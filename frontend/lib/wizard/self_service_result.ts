/**
 * Tipos e utilitários do resultado self-service (dados servidos pela API após conclusão).
 * A página pública hidrata via GET /diagnosticos/self-service/conclusao-visualizacao (PostgreSQL).
 */

import { ORDEM_DIMENSOES_API } from "@/lib/wizard/dimensao_labels";

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
  /** Narrativa LLM (somente texto) quando existir na BD e não bloqueada por guardrail. */
  explicacao_score_llm_texto?: string | null;
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
