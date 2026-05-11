import type { DiagnosticoDetalheApi } from "@/types/diagnostico_detalhe";

export type RankingGapRow = { dimensao: string; valor: number };

export function radarRowsFromScore(
  score: DiagnosticoDetalheApi["score"],
): { dimensao: string; valor: number }[] | null {
  if (!score?.score_por_dimensao) return null;
  return Object.entries(score.score_por_dimensao).map(([dim, s]) => ({
    dimensao: dim.replace(/_/g, " "),
    valor: s.valor,
  }));
}

/** Ranking por diagnóstico — menor score primeiro (maior gap). */
export function rankingGapsFromScore(score: DiagnosticoDetalheApi["score"]): RankingGapRow[] {
  if (!score?.score_por_dimensao) return [];
  return Object.entries(score.score_por_dimensao)
    .map(([dim, s]) => ({
      dimensao: dim.replace(/_/g, " "),
      valor: s.valor,
    }))
    .sort((a, b) => a.valor - b.valor);
}

/**
 * Agrega vários diagnósticos da mesma empresa: média do score por dimensão, depois ordena pelo menor (pior gap médio).
 */
export function aggregateRankingGapsEmpresa(
  detalhes: Array<{ score: DiagnosticoDetalheApi["score"] }>,
): RankingGapRow[] {
  const sums = new Map<string, { sum: number; count: number }>();
  for (const d of detalhes) {
    const sd = d.score?.score_por_dimensao;
    if (!sd) continue;
    for (const [dim, s] of Object.entries(sd)) {
      const key = dim.replace(/_/g, " ");
      const cur = sums.get(key) ?? { sum: 0, count: 0 };
      cur.sum += s.valor;
      cur.count += 1;
      sums.set(key, cur);
    }
  }
  const rows: RankingGapRow[] = [];
  sums.forEach(({ sum, count }, dimensao) => {
    if (count > 0) rows.push({ dimensao, valor: sum / count });
  });
  return rows.sort((a, b) => a.valor - b.valor);
}

export function corHeat(valor: number): string {
  if (valor < 40) return "bg-red-500/85";
  if (valor < 60) return "bg-amber-500/80";
  if (valor < 75) return "bg-yellow-400/80";
  return "bg-emerald-500/75";
}

export const BAR_GAP_COLORS = ["#b91c1c", "#ea580c", "#ca8a04", "#65a30d", "#16a34a"];
